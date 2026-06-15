from rest_framework import serializers

from .models import Expense, ExpenseShare, Settlement, Travel, TravelMember, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "openid", "nickname", "avatar_url"]


class TravelMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TravelMember
        fields = ["id", "name", "is_owner", "user"]


class ExpenseShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseShare
        fields = ["id", "member", "weight"]


class ExpenseSerializer(serializers.ModelSerializer):
    shares = ExpenseShareSerializer(many=True, read_only=True)
    payer_name = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = ["id", "title", "category", "amount", "payer", "payer_name", "note", "paid_at", "shares"]

    def get_payer_name(self, obj):
        member = obj.travel.travelmember_set.filter(user=obj.payer).first()
        return member.name if member else obj.payer.nickname


class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = ["payload"]


class TravelSerializer(serializers.ModelSerializer):
    members = TravelMemberSerializer(source="travelmember_set", many=True, read_only=True)
    expenses = ExpenseSerializer(many=True, read_only=True)
    settlement = SettlementSerializer(read_only=True)

    class Meta:
        model = Travel
        fields = [
            "id",
            "title",
            "destination",
            "currency",
            "start_date",
            "end_date",
            "status",
            "invite_code",
            "members",
            "expenses",
            "settlement",
        ]


class TravelCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    destination = serializers.CharField(required=False, allow_blank=True)
    owner_openid = serializers.CharField()
    owner_nickname = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)


class MemberCreateSerializer(serializers.Serializer):
    openid = serializers.CharField(required=False, allow_blank=True)
    nickname = serializers.CharField()


class ExpenseCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    category = serializers.CharField(required=False, allow_blank=True, default="其他")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payer_openid = serializers.CharField()
    note = serializers.CharField(required=False, allow_blank=True, default="")
    participant_openids = serializers.ListField(child=serializers.CharField(), required=False)
