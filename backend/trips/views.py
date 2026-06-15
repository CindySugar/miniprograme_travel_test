from uuid import uuid4

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Expense, ExpenseShare, Settlement, Travel, TravelMember, User
from .serializers import (
    ExpenseCreateSerializer,
    MemberCreateSerializer,
    SettlementSerializer,
    TravelCreateSerializer,
    TravelSerializer,
)
from .services import compute_settlement


def get_or_create_user(openid, nickname=""):
    if not openid:
        openid = f"temp_{uuid4().hex}"
    user, _ = User.objects.get_or_create(openid=openid, defaults={"nickname": nickname})
    if nickname and user.nickname != nickname:
        user.nickname = nickname
        user.save(update_fields=["nickname"])
    return user


class TravelViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Travel.objects.all().order_by("-created_at")
        return Response(TravelSerializer(queryset, many=True).data)

    def retrieve(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        return Response(TravelSerializer(travel).data)

    def create(self, request):
        serializer = TravelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        owner = get_or_create_user(data["owner_openid"], data.get("owner_nickname", ""))
        with transaction.atomic():
            code = get_random_string(6).upper()
            while Travel.objects.filter(invite_code=code).exists():
                code = get_random_string(6).upper()
            travel = Travel.objects.create(
                title=data["title"],
                destination=data.get("destination", ""),
                start_date=data.get("start_date"),
                invite_code=code,
                owner=owner,
            )
            TravelMember.objects.create(
                travel=travel,
                user=owner,
                name=owner.nickname or data.get("owner_nickname", "我"),
                is_owner=True,
            )
        return Response(TravelSerializer(travel).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def members(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        serializer = MemberCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = get_or_create_user(data.get("openid", ""), data["nickname"])
        member, _ = TravelMember.objects.get_or_create(
            travel=travel,
            user=user,
            defaults={"name": data["nickname"], "is_owner": False},
        )
        if member.name != data["nickname"]:
            member.name = data["nickname"]
            member.save(update_fields=["name"])
        return Response(TravelSerializer(travel).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def expenses(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payer = get_or_create_user(data["payer_openid"])
        expense = Expense.objects.create(
            travel=travel,
            title=data["title"],
            category=data.get("category") or "其他",
            amount=data["amount"],
            payer=payer,
            note=data.get("note", ""),
        )

        participant_openids = data.get("participant_openids") or [m.user.openid for m in travel.travelmember_set.all()]
        members = list(travel.travelmember_set.select_related("user").filter(user__openid__in=participant_openids))
        for member in members:
            ExpenseShare.objects.create(expense=expense, member=member, weight=1)
        return Response(TravelSerializer(travel).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def settlement(self, request, pk=None):
        travel = get_object_or_404(Travel, pk=pk)
        members = list(travel.travelmember_set.all())
        expenses = list(travel.expenses.all().prefetch_related("shares__member"))
        payload = compute_settlement(members, expenses)
        Settlement.objects.update_or_create(travel=travel, defaults={"payload": payload})
        return Response(payload)
