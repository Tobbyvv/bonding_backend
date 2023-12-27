from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from .social_views import (
    KakaoLoginView,
    AppleLoginView,
)
from .jwt_auth import TokenRefreshView
from .views import UserDetailsView, LogoutView
from profiles.views import ProfileViewSet, ScheduleViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"/schedules", ScheduleViewSet, basename="schedule")
router.register(r"/profiles", ProfileViewSet, basename="profile")

urlpatterns = [
    path("/token", TokenRefreshView.as_view(), name="token_refresh"),
    path("/login/kakao", KakaoLoginView.as_view(), name="kakao_login"),
    path("/login/apple", AppleLoginView.as_view(), name="apple_login"),
    path("/logout", LogoutView.as_view(), name="logout"),
    path("", UserDetailsView.as_view()),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += router.urls
