import json
import os
from decimal import Decimal
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4

from django.conf import settings
from django.core import signing
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Expense, ExpenseShare, Settlement, Travel, TravelMember, User, WechatBinding, default_travel_settings
from .serializers import (
    BindingSerializer,
    ExpenseCreateSerializer,
    ExpensePatchSerializer,
    JoinSerializer,
    MePatchSerializer,
    MemberCreateSerializer,
    MemberPatchSerializer,
    SettleSerializer,
    TravelCreateSerializer,
    TravelPatchSerializer,
    WechatLoginSerializer,
)
from .services import camel_settlement, compute_settlement, expense_payload, member_payload, money, settlement_detail_payload, travel_payload, user_payload


TOKEN_SALT = "wechat-session"


def ok(data=None, http_status=status.HTTP_200_OK):
    return Response({"code": 0, "message": "ok", "data": data if data is not None else {}}, status=http_status)


def token_for(identity):
    return signing.dumps(identity, salt=TOKEN_SALT)


def identity_from_request(request):
    auth = request.headers.get("Authorization", "")
    token = auth.removeprefix("Bearer ").strip() or request.headers.get("X-Session-Token", "")
    if not token:
        raise AuthenticationFailed("未登录")
    try:
        return signing.loads(token, salt=TOKEN_SALT, max_age=60 * 60 * 24 * 30)
    except signing.BadSignature as exc:
        raise AuthenticationFailed("登录失效") from exc


def current_binding(request, travel):
    identity = identity_from_request(request)
    binding = (
        WechatBinding.objects.select_related("user")
        .filter(travel=travel, appid=identity["appid"], openid=identity["openid"], is_active=True)
        .first()
    )
    return identity, binding


def require_binding(request, travel):
    identity, binding = current_binding(request, travel)
    if not binding:
        raise PermissionDenied("当前微信未绑定这次旅行")
    return identity, binding


def random_invite_code():
    code = get_random_string(6).upper()
    while Travel.objects.filter(invite_code=code).exists():
        code = get_random_string(6).upper()
    return code


def bind_wechat(travel, user, identity):
    now = timezone.now()
    if WechatBinding.objects.filter(travel=travel, appid=identity["appid"], openid=identity["openid"], is_active=True).exists():
        raise PermissionDenied("请先解绑当前微信再绑定新的成员")
    if WechatBinding.objects.filter(travel=travel, user=user, is_active=True).exists():
        raise ValidationError("该成员已被其他微信绑定")
    return WechatBinding.objects.create(
        travel=travel,
        user=user,
        appid=identity["appid"],
        openid=identity["openid"],
        unionid=identity.get("unionid", ""),
        is_active=True,
        bound_at=now,
        last_login_at=now,
    )


def share_amounts(amount, members):
    amount = money(amount)
    if not members:
        return []
    base = money(amount / len(members))
    values = [base for _ in members]
    values[-1] = amount - sum(values[:-1], Decimal("0.00"))
    return values


def parse_page(request):
    page = max(int(request.query_params.get("page", 1)), 1)
    page_size = min(max(int(request.query_params.get("pageSize", 20)), 1), 100)
    return page, page_size


@api_view(["POST"])
def wechat_login(request):
    serializer = WechatLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code = serializer.validated_data["code"]
    appid = os.environ.get("WECHAT_APPID", "dev-appid")
    secret = os.environ.get("WECHAT_SECRET", "")
    if secret:
        params = urlencode({"appid": appid, "secret": secret, "js_code": code, "grant_type": "authorization_code"})
        with urlopen(f"https://api.weixin.qq.com/sns/jscode2session?{params}", timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if "errcode" in payload:
            raise AuthenticationFailed(payload.get("errmsg", "微信登录失败"))
        openid = payload["openid"]
        unionid = payload.get("unionid", "")
    else:
        # ponytail: local dev fallback until WECHAT_APPID/WECHAT_SECRET are configured.
        openid = f"dev-{code}"
        unionid = ""
    identity = {"appid": appid, "openid": openid, "unionid": unionid}
    has_any_travel = WechatBinding.objects.filter(appid=appid, openid=openid, is_active=True).exists()
    return ok({"token": token_for(identity), "wechat": identity, "hasAnyTravel": has_any_travel})


@api_view(["GET"])
def invite_detail(request, invite_code):
    travel = get_object_or_404(Travel, invite_code=invite_code)
    claimed_user_ids = set(WechatBinding.objects.filter(travel=travel, is_active=True).values_list("user_id", flat=True))
    claimable = [
        {
            "memberId": member.id,
            "name": member.name,
            "avatarUrl": member.user.avatar_url,
            "isOwner": member.is_owner,
        }
        for member in travel.travelmember_set.select_related("user").order_by("id")
        if member.user_id not in claimed_user_ids
    ]
    return ok(
        {
            "travel": {
                "id": travel.id,
                "title": travel.title,
                "inviteCode": travel.invite_code,
                "status": travel.get_status_display(),
            },
            "claimableMembers": claimable,
        }
    )


@api_view(["POST"])
def join_travel(request):
    identity = identity_from_request(request)
    serializer = JoinSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    travel = get_object_or_404(Travel, invite_code=data["inviteCode"])
    claimed_user_ids = set(WechatBinding.objects.filter(travel=travel, is_active=True).values_list("user_id", flat=True))
    members = travel.travelmember_set.select_related("user").exclude(user_id__in=claimed_user_ids).order_by("id")
    if members.exists():
        member = members.filter(id=data.get("claimMemberId")).first()
        if not member:
            raise ValidationError("请选择可认领成员")
    else:
        nickname = (data.get("nickname") or "").strip()
        if not nickname:
            raise ValidationError("当前没有可认领成员")
        user = User.objects.create(travel=travel, nickname=nickname, avatar_url=data.get("avatarUrl", ""))
        member = TravelMember.objects.create(travel=travel, user=user, name=nickname)
    bind_wechat(travel, member.user, identity)
    return ok(travel_payload(travel))


@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_avatar(request):
    file_obj = request.FILES.get("file") or request.FILES.get("avatar")
    if not file_obj:
        raise ValidationError("file is required")
    name = default_storage.save(f"avatars/{uuid4().hex}_{file_obj.name}", file_obj)
    url = request.build_absolute_uri(settings.MEDIA_URL + name)
    return ok({"url": url, "avatarUrl": url})


class TravelViewSet(viewsets.ViewSet):
    def list(self, request):
        identity = identity_from_request(request)
        bindings = WechatBinding.objects.filter(appid=identity["appid"], openid=identity["openid"], is_active=True)
        queryset = Travel.objects.filter(id__in=bindings.values("travel_id")).order_by("-created_at")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        total = queryset.count()
        page, page_size = parse_page(request)
        travels = queryset[(page - 1) * page_size : page * page_size]
        return ok({"list": [travel_payload(travel, include_expenses=False) for travel in travels], "total": total, "page": page, "pageSize": page_size})

    def retrieve(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        return ok(travel_payload(travel))

    def create(self, request):
        identity = identity_from_request(request)
        serializer = TravelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            travel = Travel.objects.create(
                title=data["title"],
                destination=data.get("destination", ""),
                start_date=data.get("startDate"),
                end_date=data.get("endDate"),
                invite_code=random_invite_code(),
                settings={**default_travel_settings(), **data.get("settings", {})},
                advance_amount=data.get("advanceAmount"),
                cat_fund=data.get("catFund", ""),
            )
            owner = User.objects.create(travel=travel, nickname=data.get("ownerName") or "我", avatar_url=data.get("ownerAvatarUrl", ""))
            TravelMember.objects.create(travel=travel, user=owner, name=owner.nickname or "我", is_owner=True)
            travel.owner = owner
            travel.save(update_fields=["owner", "updated_at"])
            bind_wechat(travel, owner, identity)
            seen = {owner.nickname}
            for item in data.get("members", []):
                name = (item.get("nickname") or item.get("name") or "").strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                user = User.objects.create(travel=travel, nickname=name, avatar_url=item.get("avatarUrl", ""))
                TravelMember.objects.create(travel=travel, user=user, name=name)
        return ok(travel_payload(travel), status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        serializer = TravelPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        field_map = {"title": "title", "destination": "destination", "startDate": "start_date", "endDate": "end_date"}
        for incoming, model_field in field_map.items():
            if incoming in data:
                setattr(travel, model_field, data[incoming])
        if "status" in data:
            travel.status = {"进行中": "active", "已结清": "settled"}.get(data["status"], data["status"])
        if "settings" in data:
            travel.settings = {**travel.settings, **data["settings"]}
        travel.save()
        return ok(travel_payload(travel))

    @action(detail=True, methods=["get", "patch"], url_path="me")
    def me(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        identity, binding = current_binding(request, travel)
        if request.method == "GET":
            return ok(
                {
                    "bound": bool(binding),
                    "wechat": {"appid": identity["appid"], "openid": identity["openid"], "unionid": identity.get("unionid", "")},
                    "user": user_payload(binding.user) if binding else None,
                    "binding": {"id": binding.id, "userId": binding.user_id, "boundAt": binding.bound_at.isoformat()} if binding else None,
                }
            )
        if not binding:
            raise PermissionDenied("当前微信未绑定这次旅行")
        serializer = MePatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "nickname" in data:
            binding.user.nickname = data["nickname"]
            member = TravelMember.objects.filter(travel=travel, user=binding.user).first()
            if member:
                member.name = data["nickname"]
                member.save(update_fields=["name", "updated_at"])
        if "avatarUrl" in data:
            binding.user.avatar_url = data["avatarUrl"]
        binding.user.save(update_fields=["nickname", "avatar_url", "updated_at"])
        return ok({"bound": True, "user": user_payload(binding.user)})

    @action(detail=True, methods=["post", "patch", "delete"], url_path="binding")
    def binding(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        identity = identity_from_request(request)
        if request.method == "DELETE":
            WechatBinding.objects.filter(travel=travel, appid=identity["appid"], openid=identity["openid"], is_active=True).update(
                is_active=False, unbound_at=timezone.now()
            )
            return ok({"bound": False})
        serializer = BindingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, pk=serializer.validated_data["userId"], travel=travel)
        if WechatBinding.objects.filter(travel=travel, appid=identity["appid"], openid=identity["openid"], is_active=True).exists():
            raise PermissionDenied("请先解绑当前微信再绑定新的成员")
        bind_wechat(travel, user, identity)
        return ok({"bound": True, "user": user_payload(user)})

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        if request.method == "GET":
            claimed_user_ids = set(WechatBinding.objects.filter(travel=travel, is_active=True).values_list("user_id", flat=True))
            return ok({"list": [member_payload(member, claimed_user_ids) for member in travel.travelmember_set.select_related("user").order_by("id")]})
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            if data.get("userId"):
                user = get_object_or_404(User, pk=data["userId"], travel=travel)
                member, created = TravelMember.objects.get_or_create(travel=travel, user=user, defaults={"name": user.nickname or data.get("nickname") or data.get("name", "")})
                if not created:
                    raise ValidationError("成员已存在")
            else:
                name = (data.get("nickname") or data.get("name") or "").strip()
                user = User.objects.create(travel=travel, nickname=name, avatar_url=data.get("avatarUrl", ""))
                TravelMember.objects.create(travel=travel, user=user, name=name)
        return ok(travel_payload(travel), status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path=r"members/(?P<member_id>[^/.]+)")
    def member_detail(self, request, pk=None, member_id=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        member = get_object_or_404(TravelMember.objects.select_related("user"), pk=member_id, travel=travel)
        if request.method == "DELETE":
            if member.is_owner:
                raise ValidationError("管理员不能移出组队")
            member.user.delete()
            return ok(travel_payload(travel))
        serializer = MemberPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        name = data.get("nickname") or data.get("name")
        if name is not None:
            member.name = name
            member.user.nickname = name
        if "avatarUrl" in data:
            member.user.avatar_url = data["avatarUrl"]
        if "canBookkeep" in data:
            member.can_bookkeep = data["canBookkeep"]
        if "status" in data:
            member.user.status = data["status"]
        member.user.save()
        member.save()
        return ok(member_payload(member))

    @action(detail=True, methods=["post"], url_path=r"members/(?P<member_id>[^/.]+)/clear-claim")
    def clear_claim(self, request, pk=None, member_id=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        member = get_object_or_404(TravelMember, pk=member_id, travel=travel)
        if member.is_owner:
            raise ValidationError("管理员不能清除认领")
        WechatBinding.objects.filter(travel=travel, user=member.user, is_active=True).update(is_active=False, unbound_at=timezone.now())
        return ok(travel_payload(travel))

    @action(detail=True, methods=["get", "post"], url_path="expenses")
    def expenses(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        if request.method == "GET":
            queryset = travel.expenses.select_related("payer_member__user").prefetch_related("shares__member__user").order_by("-created_at", "-id")
            if request.query_params.get("payerMemberId"):
                queryset = queryset.filter(payer_member_id=request.query_params["payerMemberId"])
            if request.query_params.get("splitType"):
                queryset = queryset.filter(split_type=request.query_params["splitType"])
            total = queryset.count()
            page, page_size = parse_page(request)
            return ok({"list": [expense_payload(item) for item in queryset[(page - 1) * page_size : page * page_size]], "total": total, "page": page, "pageSize": page_size})

        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payer_member_id = data.get("payerMemberId") or data.get("payerId")
        payer = get_object_or_404(TravelMember, pk=payer_member_id, travel=travel)
        if not payer.can_bookkeep or payer.user.status != "enabled":
            raise PermissionDenied("该成员不能记账")
        participant_ids = data.get("participantMemberIds") or data.get("participantIds")
        participants = list(travel.travelmember_set.select_related("user").filter(id__in=participant_ids)) if participant_ids else list(travel.travelmember_set.select_related("user"))
        if not participants:
            raise ValidationError("participantMemberIds is required")
        with transaction.atomic():
            expense = Expense.objects.create(
                travel=travel,
                title=data["title"],
                category=data.get("category") or "其他",
                amount=data["amount"],
                payer_member=payer,
                split_type=data.get("splitType", "equal"),
                note=data.get("note", ""),
                paid_at=data.get("paidAt"),
            )
            amounts = share_amounts(data["amount"], participants)
            for member, share_amount in zip(participants, amounts):
                ExpenseShare.objects.create(expense=expense, member=member, weight=1, share_amount=share_amount)
        return ok(expense_payload(expense), status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch", "delete"], url_path=r"expenses/(?P<expense_id>[^/.]+)")
    def expense_detail(self, request, pk=None, expense_id=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        expense = get_object_or_404(Expense.objects.select_related("payer_member__user").prefetch_related("shares__member__user"), pk=expense_id, travel=travel)
        if request.method == "DELETE":
            expense.delete()
            return ok({})
        if request.method == "PATCH":
            serializer = ExpensePatchSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            existing_participants = list(expense.shares.select_related("member__user").order_by("id"))
            if "title" in data:
                expense.title = data["title"]
            if "category" in data:
                expense.category = data["category"] or "其他"
            if "amount" in data:
                expense.amount = data["amount"]
            if "note" in data:
                expense.note = data["note"]
            if "paidAt" in data:
                expense.paid_at = data["paidAt"]
            if "splitType" in data:
                expense.split_type = data["splitType"]
            payer_member_id = data.get("payerMemberId") or data.get("payerId")
            if payer_member_id:
                expense.payer_member = get_object_or_404(TravelMember, pk=payer_member_id, travel=travel)
            participant_ids = data.get("participantMemberIds") or data.get("participantIds")
            participants = list(travel.travelmember_set.select_related("user").filter(id__in=participant_ids)) if participant_ids else [share.member for share in existing_participants]
            expense.save()
            expense.shares.all().delete()
            if participants:
                for member, share_amount in zip(participants, share_amounts(expense.amount, participants)):
                    ExpenseShare.objects.create(expense=expense, member=member, weight=1, share_amount=share_amount)
            return ok(expense_payload(expense))
        return ok(expense_payload(expense))

    @action(detail=True, methods=["get"], url_path="settlement")
    def settlement(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        members = list(travel.travelmember_set.select_related("user").order_by("id"))
        expenses = list(travel.expenses.select_related("payer_member__user").prefetch_related("shares__member__user"))
        payload = compute_settlement(members, expenses)
        Settlement.objects.update_or_create(travel=travel, defaults={"payload": payload})
        return ok(camel_settlement(payload))

    @action(detail=True, methods=["get"], url_path="settlement/detail")
    def settlement_detail(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        return ok(settlement_detail_payload(travel))

    @action(detail=True, methods=["post"], url_path="settle")
    def settle(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        require_binding(request, travel)
        serializer = SettleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        travel.status = "settled"
        if serializer.validated_data.get("endDate"):
            travel.end_date = serializer.validated_data["endDate"]
        travel.save()
        return ok(travel_payload(travel))
