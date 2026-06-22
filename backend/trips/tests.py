from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Expense, ExpenseShare, Travel, TravelMember, User, WechatBinding
from .services import compute_settlement
from .views import token_for


class SettlementTests(TestCase):
    def setUp(self):
        self.travel = Travel.objects.create(title="Trip", invite_code="ABC123")
        self.owner = User.objects.create(travel=self.travel, nickname="A")
        self.b = User.objects.create(travel=self.travel, nickname="B")
        self.c = User.objects.create(travel=self.travel, nickname="C")
        self.travel.owner = self.owner
        self.travel.save()
        self.m1 = TravelMember.objects.create(travel=self.travel, user=self.owner, name="A", is_owner=True)
        self.m2 = TravelMember.objects.create(travel=self.travel, user=self.b, name="B", is_owner=False)
        self.m3 = TravelMember.objects.create(travel=self.travel, user=self.c, name="C", is_owner=False)

    def test_equal_split(self):
        expense = Expense.objects.create(travel=self.travel, title="Dinner", amount=Decimal("90.00"), payer_member=self.m1)
        ExpenseShare.objects.create(expense=expense, member=self.m1, weight=1, share_amount=Decimal("30.00"))
        ExpenseShare.objects.create(expense=expense, member=self.m2, weight=1, share_amount=Decimal("30.00"))
        ExpenseShare.objects.create(expense=expense, member=self.m3, weight=1, share_amount=Decimal("30.00"))

        payload = compute_settlement([self.m1, self.m2, self.m3], [expense])
        nets = [Decimal(row["net"]) for row in payload["balances"]]
        self.assertEqual(sum(nets), Decimal("0.00"))
        self.assertEqual(payload["total_spent"], "90.00")

    def test_partial_participants(self):
        expense = Expense.objects.create(travel=self.travel, title="Taxi", amount=Decimal("30.00"), payer_member=self.m2)
        ExpenseShare.objects.create(expense=expense, member=self.m1, weight=1, share_amount=Decimal("15.00"))
        ExpenseShare.objects.create(expense=expense, member=self.m2, weight=1, share_amount=Decimal("15.00"))

        payload = compute_settlement([self.m1, self.m2, self.m3], [expense])
        self.assertEqual(Decimal(payload["total_spent"]), Decimal("30.00"))
        self.assertEqual(len(payload["transfers"]), 1)


class TravelApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.identity = {"appid": "dev-appid", "openid": "dev-code-a", "unionid": ""}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_for(self.identity)}")

    def test_create_list_expense_settlement_flow(self):
        response = self.client.post(
            "/api/travels/",
            {
                "title": "杭州周末游",
                "ownerName": "我",
                "members": [{"name": "小路"}, {"name": "阿毛"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        travel = response.data["data"]
        self.assertEqual(travel["memberCount"], 3)
        self.assertTrue(WechatBinding.objects.filter(openid="dev-code-a", travel_id=travel["id"], is_active=True).exists())

        list_response = self.client.get("/api/travels/")
        self.assertEqual(list_response.data["data"]["total"], 1)

        payer_id = travel["members"][0]["id"]
        participant_ids = [member["id"] for member in travel["members"]]
        expense_response = self.client.post(
            f"/api/travels/{travel['id']}/expenses/",
            {
                "title": "晚餐",
                "category": "餐饮",
                "amount": "90.00",
                "payerMemberId": payer_id,
                "participantMemberIds": participant_ids,
            },
            format="json",
        )
        self.assertEqual(expense_response.status_code, 201)
        self.assertEqual(expense_response.data["data"]["participantShares"][0]["shareAmount"], "30.00")

        settlement_response = self.client.get(f"/api/travels/{travel['id']}/settlement/")
        self.assertEqual(settlement_response.data["data"]["totalSpent"], "90.00")
        self.assertEqual(len(settlement_response.data["data"]["transfers"]), 2)

        detail_response = self.client.get(f"/api/travels/{travel['id']}/settlement/detail/")
        self.assertEqual(detail_response.data["data"]["balances"][0]["sourceExpenses"][0]["title"], "晚餐")

        patch_response = self.client.patch(
            f"/api/travels/{travel['id']}/expenses/{expense_response.data['data']['expenseId']}/",
            {
                "title": "改过的晚餐",
                "amount": "60.00",
                "participantMemberIds": participant_ids[:2],
            },
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["data"]["title"], "改过的晚餐")
        self.assertEqual(patch_response.data["data"]["participantShares"][0]["shareAmount"], "30.00")

        delete_response = self.client.delete(f"/api/travels/{travel['id']}/expenses/{expense_response.data['data']['expenseId']}/")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.data["code"], 0)

    def test_list_filters_by_active_wechat_binding(self):
        other_travel = Travel.objects.create(title="Other", invite_code="OTHER1")
        other_user = User.objects.create(travel=other_travel, nickname="Other")
        other_travel.owner = other_user
        other_travel.save()
        WechatBinding.objects.create(travel=other_travel, user=other_user, appid="dev-appid", openid="someone-else")

        response = self.client.get("/api/travels/")
        self.assertEqual(response.data["data"]["total"], 0)

    def test_documented_paths_work_without_trailing_slash(self):
        response = self.client.post("/api/travels", {"title": "No Slash", "ownerName": "Owner"}, format="json")
        self.assertEqual(response.status_code, 201)
        travel_id = response.data["data"]["id"]
        me = self.client.get(f"/api/travels/{travel_id}/me")
        self.assertTrue(me.data["data"]["bound"])

    def test_join_creates_user_when_no_claimable_member(self):
        create = self.client.post(
            "/api/travels/",
            {"title": "Invite Trip", "ownerName": "Owner"},
            format="json",
        )
        travel = create.data["data"]
        join_client = APIClient()
        join_identity = {"appid": "dev-appid", "openid": "dev-code-b", "unionid": ""}
        join_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_for(join_identity)}")
        response = join_client.post(
            "/api/travels/join",
            {"inviteCode": travel["inviteCode"], "nickname": "新成员", "avatarUrl": "avatar.png"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["memberCount"], 2)
        self.assertTrue(WechatBinding.objects.filter(travel_id=travel["id"], openid="dev-code-b", is_active=True).exists())

    def test_join_requires_claim_member_when_any_claimable_exists(self):
        create = self.client.post(
            "/api/travels/",
            {"title": "Invite Trip", "ownerName": "Owner", "members": [{"name": "B"}]},
            format="json",
        )
        travel = create.data["data"]
        join_client = APIClient()
        join_login = join_client.post("/api/auth/wechat-login", {"code": "invite-claim-c"}, format="json")
        join_client.credentials(HTTP_AUTHORIZATION=f"Bearer {join_login.data['data']['token']}")
        response = join_client.post(
            "/api/travels/join",
            {"inviteCode": travel["inviteCode"], "nickname": "新成员", "avatarUrl": "avatar.png"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_binding_requires_unbind_first(self):
        create = self.client.post(
            "/api/travels/",
            {"title": "Bind Trip", "ownerName": "Owner", "members": [{"name": "B"}]},
            format="json",
        )
        travel = create.data["data"]
        user_id = travel["members"][1]["userId"]
        response = self.client.post(
            f"/api/travels/{travel['id']}/binding",
            {"userId": user_id},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
