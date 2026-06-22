from decimal import Decimal, ROUND_HALF_UP

from .models import WechatBinding


def money(value):
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def camel_settlement(payload):
    return {
        "totalSpent": payload["total_spent"],
        "balances": [
            {
                "memberId": row["member_id"],
                "name": row["name"],
                "paid": row["paid"],
                "owed": row["owed"],
                "net": row["net"],
            }
            for row in payload["balances"]
        ],
        "transfers": [
            {
                "fromMemberId": row["from_member_id"],
                "fromName": row["from_name"],
                "toMemberId": row["to_member_id"],
                "toName": row["to_name"],
                "amount": row["amount"],
            }
            for row in payload["transfers"]
        ],
    }


def compute_settlement(members, expenses):
    balances = {
        member.id: {
            "member_id": member.id,
            "name": member.name,
            "paid": Decimal("0.00"),
            "owed": Decimal("0.00"),
        }
        for member in members
    }

    for expense in expenses:
        payer = balances.get(expense.payer_member_id)
        if payer:
            payer["paid"] += money(expense.amount)

        shares = list(expense.shares.select_related("member"))
        if not shares:
            shares = [type("Share", (), {"member_id": member.id, "weight": Decimal("1.00"), "share_amount": None})() for member in members]

        if expense.split_type == "amount" and all(share.share_amount is not None for share in shares):
            for share in shares:
                balances[share.member_id]["owed"] += money(share.share_amount)
            continue

        total_weight = sum(Decimal(share.weight) for share in shares)
        if total_weight <= 0:
            continue
        distributed = Decimal("0.00")
        for index, share in enumerate(shares):
            amount = money(expense.amount) - distributed if index == len(shares) - 1 else money(money(expense.amount) * Decimal(share.weight) / total_weight)
            distributed += amount
            balances[share.member_id]["owed"] += amount

    rows = []
    for row in balances.values():
        row["net"] = money(row["paid"] - row["owed"])
        rows.append(row)

    creditors = sorted([row.copy() for row in rows if row["net"] > 0], key=lambda item: item["net"], reverse=True)
    debtors = sorted([row.copy() for row in rows if row["net"] < 0], key=lambda item: item["net"])
    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        amount = money(min(-debtor["net"], creditor["net"]))
        if amount <= 0:
            break
        transfers.append(
            {
                "from_member_id": debtor["member_id"],
                "from_name": debtor["name"],
                "to_member_id": creditor["member_id"],
                "to_name": creditor["name"],
                "amount": str(amount),
            }
        )
        debtor["net"] += amount
        creditor["net"] -= amount
        if abs(debtor["net"]) < Decimal("0.005"):
            i += 1
        if abs(creditor["net"]) < Decimal("0.005"):
            j += 1

    return {
        "balances": [
            {
                **row,
                "paid": str(money(row["paid"])),
                "owed": str(money(row["owed"])),
                "net": str(money(row["net"])),
            }
            for row in rows
        ],
        "transfers": transfers,
        "total_spent": str(money(sum((expense.amount for expense in expenses), Decimal("0.00")))),
    }


def member_payload(member, claimed_user_ids=None):
    claimed_user_ids = claimed_user_ids or set()
    return {
        "id": member.id,
        "userId": member.user_id,
        "user": user_payload(member.user),
        "name": member.name,
        "avatarUrl": member.user.avatar_url,
        "isOwner": member.is_owner,
        "claimed": member.user_id in claimed_user_ids,
        "canBookkeep": member.can_bookkeep,
    }


def user_payload(user):
    return {
        "id": user.id,
        "travelId": user.travel_id,
        "nickname": user.nickname,
        "avatarUrl": user.avatar_url,
        "status": user.status,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
    }


def expense_payload(expense):
    shares = list(expense.shares.select_related("member__user"))
    return {
        "id": expense.id,
        "expenseId": expense.id,
        "title": expense.title,
        "category": expense.category,
        "amount": str(money(expense.amount)),
        "payerMemberId": expense.payer_member_id,
        "payerUserId": expense.payer_member.user_id,
        "payerName": expense.payer_member.name,
        "payerAvatarUrl": expense.payer_member.user.avatar_url,
        "splitType": expense.split_type,
        "participants": [
            {
                "memberId": share.member_id,
                "name": share.member.name,
                "avatarUrl": share.member.user.avatar_url,
            }
            for share in shares
        ],
        "participantShares": [
            {
                "memberId": share.member_id,
                "name": share.member.name,
                "shareAmount": str(money(share.share_amount or 0)),
            }
            for share in shares
        ],
        "note": expense.note,
        "paidAt": (expense.paid_at or expense.created_at).isoformat() if (expense.paid_at or expense.created_at) else None,
        "createdAt": expense.created_at.isoformat() if expense.created_at else None,
        "editable": expense.travel.status == "active",
    }


def travel_payload(travel, include_expenses=True):
    members = list(travel.travelmember_set.select_related("user").order_by("id"))
    claimed_user_ids = set(
        WechatBinding.objects.filter(travel=travel, is_active=True, user_id__in=[member.user_id for member in members]).values_list("user_id", flat=True)
    )
    expenses = list(travel.expenses.select_related("payer_member__user").prefetch_related("shares__member__user").order_by("-created_at", "-id"))
    settlement = camel_settlement(compute_settlement(members, expenses))
    payload = {
        "id": travel.id,
        "title": travel.title,
        "destination": travel.destination,
        "currency": travel.currency,
        "startDate": travel.start_date.isoformat() if travel.start_date else "",
        "endDate": travel.end_date.isoformat() if travel.end_date else "",
        "status": travel.get_status_display(),
        "statusCode": travel.status,
        "inviteCode": travel.invite_code,
        "ownerUserId": travel.owner_id,
        "createdAt": travel.created_at.isoformat() if travel.created_at else None,
        "updatedAt": travel.updated_at.isoformat() if travel.updated_at else None,
        "members": [member_payload(member, claimed_user_ids) for member in members],
        "memberCount": len(members),
        "expenseCount": len(expenses),
        "summary": settlement,
        "settings": {
            **travel.settings,
            "advanceAmount": str(money(travel.advance_amount)) if travel.advance_amount is not None else "",
            "catFund": travel.cat_fund,
        },
    }
    if include_expenses:
        payload["expenses"] = [expense_payload(expense) for expense in expenses]
    return payload


def settlement_detail_payload(travel):
    members = list(travel.travelmember_set.select_related("user").order_by("id"))
    expenses = list(travel.expenses.select_related("payer_member__user").prefetch_related("shares__member__user").order_by("-created_at", "-id"))
    settlement = camel_settlement(compute_settlement(members, expenses))
    source_by_member = {member.id: [] for member in members}
    for expense in expenses:
        for share in expense.shares.select_related("member"):
            source_by_member.setdefault(share.member_id, []).append(
                {
                    "expenseId": expense.id,
                    "title": expense.title,
                    "category": expense.category,
                    "amount": str(money(expense.amount)),
                    "shareAmount": str(money(share.share_amount or 0)),
                    "payerMemberId": expense.payer_member_id,
                    "payerName": expense.payer_member.name,
                    "paidAt": (expense.paid_at or expense.created_at).isoformat() if (expense.paid_at or expense.created_at) else None,
                }
            )
    for row in settlement["balances"]:
        net = money(row["net"])
        row["netType"] = "receivable" if net > 0 else "payable" if net < 0 else "settled"
        row["sourceExpenses"] = source_by_member.get(row["memberId"], [])
    return settlement
