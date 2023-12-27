from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework.generics import (
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .exceptions import (
    SkipTokenException,
    InvalidTokenException,
)
from teampang.exceptions import ServerException
from .serializers import UserDetailsSerializer
from .social_views import KaKaoDisconnectView


class UserDetailsView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserDetailsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = {"message": "사용자 조회 성공"}
        data.update(serializer.data)
        return Response(data)

    def get_queryset(self):
        return get_user_model().objects.none()

    def disconnect_profile(self, user):
        try:
            profile = user.profile
            profile.user = None
            profile.save()
        except Exception:
            pass

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.disconnect_profile(instance)

        if instance.user_type == "K":
            KaKaoDisconnectView.disconnect(KaKaoDisconnectView, instance)
        LogoutView.logout(LogoutView, request)
        self.perform_destroy(instance)
        return Response(status=204)


class LogoutView(GenericAPIView):
    """
    expires both the user access token and the refresh token.
    """

    permission_classes = (IsAuthenticated,)

    def logout(self, request):
        response = Response({"message": _("로그아웃 성공.")}, status=200)

        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            refresh = RefreshToken(request.data["refresh"])
            refresh.blacklist()
        except KeyError:
            raise SkipTokenException
        except (TokenError, AttributeError, TypeError) as error:
            if hasattr(error, "args"):
                if (
                    "Token is blacklisted" in error.args
                    or "Token is invalid or expired" in error.args
                ):
                    raise InvalidTokenException
                else:
                    raise ServerException
            else:
                raise ServerException

        return response

    def post(self, request, *args, **kwargs):
        return self.logout(request)
