import datetime
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.utils import datetime_from_epoch
from .exceptions import (
    SkipTokenException,
    InvalidTokenException,
)
from teampang.exceptions import ServerException

REFRESH_TOKEN_SLIDE = timedelta(days=60)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class TokenRefreshWithExtendSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def check_exp(self, refresh):
        refresh_exp = datetime_from_epoch(refresh.payload["exp"])
        available_exp = (refresh_exp - datetime.timedelta(days=30)).timestamp()
        now = timezone.now().timestamp()
        return now > available_exp

    def validate(self, attrs):

        try:
            refresh = RefreshToken(attrs["refresh"])
            data = {"access": str(refresh.access_token)}

            if self.check_exp(refresh):
                refresh.set_exp(lifetime=REFRESH_TOKEN_SLIDE)

            data.update({"message": "토큰 재발급 성공"})
            return data
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


class TokenRefreshView(TokenViewBase):
    serializer_class = TokenRefreshWithExtendSerializer
