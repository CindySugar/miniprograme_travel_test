from decimal import Decimal

from django.test import TestCase

from .models import Expense, ExpenseShare, Travel, TravelMember, User
from .services import compute_settlement


class SettlementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create(openid="u1", nickname="A")
        self.b = User.objects.create(openid="u2", nickname="B")
        self.c = User.objects.create(openid="u3", nickname="C")
        self.travel = Travel.objects.create(title="Trip", invite_code="ABC123", owner=self.owner)
        self.m1 = TravelMember.objects.create(travel=self.travel, user=self.owner, name="A", is_owner=True)
        self.m2 = TravelMember.objects.create(travel=self.travel, user=self.b, name="B", is_owner=False)
        self.m3 = TravelMember.objects.create(travel=self.travel, user=self.c, name="C", is_owner=False)

    def test_equal_split(self):
        expense = Expense.objects.create(travel=self.travel, title="Dinner", amount=Decimal("90.00"), payer=self.owner)
        ExpenseShare.objects.create(expense=expense, member=self.m1, weight=1)
        ExpenseShare.objects.create(expense=expense, member=self.m2, weight=1)
        ExpenseShare.objects.create(expense=expense, member=self.m3, weight=1)

        payload = compute_settlement([self.m1, self.m2, self.m3], [expense])
        nets = [Decimal(row["net"]) for row in payload["balances"]]
        self.assertEqual(sum(nets), Decimal("0.00"))

    def test_partial_participants(self):
        expense = Expense.objects.create(travel=self.travel, title="Taxi", amount=Decimal("30.00"), payer=self.b)
        ExpenseShare.objects.create(expense=expense, member=self.m1, weight=1)
        ExpenseShare.objects.create(expense=expense, member=self.m2, weight=1)
        payload = compute_settlement([self.m1, self.m2, self.m3], [expense])
        self.assertEqual(Decimal(payload["total_spent"]), Decimal("30.00"))
        self.assertEqual(len(payload["transfers"]), 1)
