from rest_framework import serializers


class WechatLoginSerializer(serializers.Serializer):
    code = serializers.CharField()
    nickname = serializers.CharField(required=False, allow_blank=True)
    avatarUrl = serializers.CharField(required=False, allow_blank=True)


class TravelCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    destination = serializers.CharField(required=False, allow_blank=True, default="")
    startDate = serializers.DateField(required=False)
    endDate = serializers.DateField(required=False)
    ownerName = serializers.CharField(required=False, allow_blank=True, default="我")
    ownerAvatarUrl = serializers.CharField(required=False, allow_blank=True, default="")
    members = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    advanceAmount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    catFund = serializers.CharField(required=False, allow_blank=True, default="")
    settings = serializers.DictField(required=False, default=dict)


class TravelPatchSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    destination = serializers.CharField(required=False, allow_blank=True)
    startDate = serializers.DateField(required=False, allow_null=True)
    endDate = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=["active", "settled", "进行中", "已结清"], required=False)
    settings = serializers.DictField(required=False)


class MemberCreateSerializer(serializers.Serializer):
    userId = serializers.IntegerField(required=False)
    nickname = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    avatarUrl = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("userId") and not (attrs.get("nickname") or attrs.get("name")):
            raise serializers.ValidationError("nickname is required")
        return attrs


class MemberPatchSerializer(serializers.Serializer):
    nickname = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    avatarUrl = serializers.CharField(required=False, allow_blank=True)
    canBookkeep = serializers.BooleanField(required=False)
    status = serializers.ChoiceField(choices=["enabled", "disabled"], required=False)


class BindingSerializer(serializers.Serializer):
    userId = serializers.IntegerField()


class MePatchSerializer(serializers.Serializer):
    nickname = serializers.CharField(required=False, allow_blank=True)
    avatarUrl = serializers.CharField(required=False, allow_blank=True)


class ExpenseCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    category = serializers.CharField(required=False, allow_blank=True, default="其他")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payerMemberId = serializers.IntegerField(required=False)
    payerId = serializers.IntegerField(required=False)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    participantMemberIds = serializers.ListField(child=serializers.IntegerField(), required=False)
    participantIds = serializers.ListField(child=serializers.IntegerField(), required=False)
    paidAt = serializers.DateTimeField(required=False)
    splitType = serializers.ChoiceField(choices=["equal", "amount"], required=False, default="equal")

    def validate(self, attrs):
        if attrs["amount"] <= 0:
            raise serializers.ValidationError("amount must be greater than 0")
        if not attrs.get("payerMemberId") and not attrs.get("payerId"):
            raise serializers.ValidationError("payerMemberId is required")
        return attrs


class ExpensePatchSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    category = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    payerMemberId = serializers.IntegerField(required=False)
    payerId = serializers.IntegerField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)
    participantMemberIds = serializers.ListField(child=serializers.IntegerField(), required=False)
    participantIds = serializers.ListField(child=serializers.IntegerField(), required=False)
    paidAt = serializers.DateTimeField(required=False)
    splitType = serializers.ChoiceField(choices=["equal", "amount"], required=False)

    def validate(self, attrs):
        if "amount" in attrs and attrs["amount"] <= 0:
            raise serializers.ValidationError("amount must be greater than 0")
        return attrs


class JoinSerializer(serializers.Serializer):
    inviteCode = serializers.CharField()
    claimMemberId = serializers.IntegerField(required=False)
    nickname = serializers.CharField(required=False, allow_blank=True)
    avatarUrl = serializers.CharField(required=False, allow_blank=True, default="")


class SettleSerializer(serializers.Serializer):
    endDate = serializers.DateField(required=False)
