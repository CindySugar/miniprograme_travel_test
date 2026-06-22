from django.db import models
from django.utils import timezone


def default_travel_settings():
    return {
        "allowInvite": True,
        "allowMemberFamilyEdit": True,
        "allowInvitedIdentity": True,
        "requireAvatar": False,
    }


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimeStampedModel):
    STATUS_CHOICES = [
        ("enabled", "启用"),
        ("disabled", "禁用"),
    ]

    travel = models.ForeignKey("Travel", on_delete=models.CASCADE, related_name="users", null=True, blank=True)
    nickname = models.CharField(max_length=64, blank=True, default="")
    avatar_url = models.CharField(max_length=512, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="enabled")

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.nickname or f"user-{self.pk}"


class Travel(TimeStampedModel):
    STATUS_CHOICES = [
        ("active", "进行中"),
        ("settled", "已结清"),
    ]

    title = models.CharField(max_length=128)
    destination = models.CharField(max_length=128, blank=True, default="")
    currency = models.CharField(max_length=8, default="CNY")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active")
    invite_code = models.CharField(max_length=16, unique=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="owned_travels", null=True, blank=True)
    members = models.ManyToManyField(User, through="TravelMember", related_name="travels")
    settings = models.JSONField(default=default_travel_settings)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cat_fund = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        db_table = "travels"

    def __str__(self):
        return self.title


class WechatBinding(TimeStampedModel):
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE, related_name="wechat_bindings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wechat_bindings")
    appid = models.CharField(max_length=128)
    openid = models.CharField(max_length=128)
    unionid = models.CharField(max_length=128, blank=True, default="")
    is_active = models.BooleanField(default=True)
    bound_at = models.DateTimeField(default=timezone.now)
    unbound_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "wechat_bindings"
        indexes = [
            models.Index(fields=["travel", "appid", "openid", "is_active"]),
            models.Index(fields=["travel", "user", "is_active"]),
        ]


class TravelMember(TimeStampedModel):
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    is_owner = models.BooleanField(default=False)
    can_bookkeep = models.BooleanField(default=True)

    class Meta:
        db_table = "travel_members"
        unique_together = ("travel", "user")


class Expense(TimeStampedModel):
    SPLIT_CHOICES = [
        ("equal", "平摊"),
        ("amount", "按金额"),
    ]

    travel = models.ForeignKey(Travel, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=128)
    category = models.CharField(max_length=64, blank=True, default="其他")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payer_member = models.ForeignKey(TravelMember, on_delete=models.CASCADE, related_name="paid_expenses", null=True)
    split_type = models.CharField(max_length=16, choices=SPLIT_CHOICES, default="equal")
    note = models.TextField(blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "expenses"

    def __str__(self):
        return self.title


class ExpenseShare(TimeStampedModel):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="shares")
    member = models.ForeignKey(TravelMember, on_delete=models.CASCADE, related_name="shares")
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    share_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "expense_shares"
        unique_together = ("expense", "member")


class Settlement(TimeStampedModel):
    travel = models.OneToOneField(Travel, on_delete=models.CASCADE, related_name="settlement")
    payload = models.JSONField(default=dict)

    class Meta:
        db_table = "settlements"
