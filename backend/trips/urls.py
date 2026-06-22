from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

from .views import TravelViewSet, invite_detail, join_travel, upload_avatar, wechat_login

router = DefaultRouter()
router.trailing_slash = "/?"
router.register(r"travels", TravelViewSet, basename="travel")

urlpatterns = [
    re_path(r"^auth/wechat-login/?$", wechat_login),
    re_path(r"^invites/(?P<invite_code>[^/]+)/?$", invite_detail),
    re_path(r"^travels/join/?$", join_travel),
    re_path(r"^uploads/avatar/?$", upload_avatar),
    re_path(r"^", include(router.urls)),
]
