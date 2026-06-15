from decimal import Decimal, ROUND_HALF_UP


def quantize_money(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
        payer = balances.get(expense.payer_id)
        if payer:
            payer["paid"] += quantize_money(expense.amount)

        shares = list(expense.shares.select_related("member")) or []
        if not shares:
            shares = []
            for member in members:
                shares.append(type("Share", (), {"member_id": member.id, "weight": Decimal("1.00")})())

        total_weight = sum(Decimal(share.weight) for share in shares)
        distributed = Decimal("0.00")
        for index, share in enumerate(shares):
            if index == len(shares) - 1:
                amount = quantize_money(expense.amount) - distributed
            else:
                amount = quantize_money(quantize_money(expense.amount) * Decimal(share.weight) / total_weight)
            distributed += amount
            balances[share.member_id]["owed"] += amount

    rows = []
    for row in balances.values():
        row["net"] = quantize_money(row["paid"] - row["owed"])
        rows.append(row)

    creditors = sorted([row.copy() for row in rows if row["net"] > 0], key=lambda item: item["net"], reverse=True)
    debtors = sorted([row.copy() for row in rows if row["net"] < 0], key=lambda item: item["net"])
    transfers = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor = debtors[i]
        creditor = creditors[j]
        amount = min(-debtor["net"], creditor["net"])
        amount = quantize_money(amount)
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
                "paid": str(quantize_money(row["paid"])),
                "owed": str(quantize_money(row["owed"])),
                "net": str(quantize_money(row["net"])),
            }
            for row in rows
        ],
        "transfers": transfers,
        "total_spent": str(quantize_money(sum((expense.amount for expense in expenses), Decimal("0.00")))),
    }
