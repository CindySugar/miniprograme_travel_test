from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimeStampedModel):
    openid = models.CharField(max_length=128, unique=True)
    nickname = models.CharField(max_length=64, blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")

    def __str__(self):
        return self.nickname or self.openid


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
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_travels")
    members = models.ManyToManyField(User, through="TravelMember", related_name="travels")

    def __str__(self):
        return self.title


class TravelMember(TimeStampedModel):
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    is_owner = models.BooleanField(default=False)

    class Meta:
        unique_together = ("travel", "user")


class Expense(TimeStampedModel):
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE, related_name="expenses")
    title = models.CharField(max_length=128)
    category = models.CharField(max_length=64, blank=True, default="其他")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="paid_expenses")
    note = models.TextField(blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class ExpenseShare(TimeStampedModel):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="shares")
    member = models.ForeignKey(TravelMember, on_delete=models.CASCADE, related_name="shares")
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=1)


class Settlement(TimeStampedModel):
    travel = models.OneToOneField(Travel, on_delete=models.CASCADE, related_name="settlement")
    payload = models.JSONField(default=dict)
