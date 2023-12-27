from .exceptions import ExistEmailException
from django.db import IntegrityError
from django.utils import timezone
from .models import User


class Provider(object):
    with_deleted = {"deleted": False}
    queryset = User.objects.get_queryset(**with_deleted)

    def __init__(self, request):
        self.request = request

    @classmethod
    def sociallogin(self, data):

        social_id = self.extract_uid(data)
        email = self.extract_email(data)
        user_type = self.user_type
        p_id = self.id

        try:
            if email is None:
                raise User.DoesNotExist

            user = self.queryset.get(email=email)  # email exist

            # old user
            if (user.user_type == user_type) and (user.social_id == social_id):
                # # soft deleted user
                # if not user.is_active:
                #     user.restore()
                user.last_login = timezone.now()
                user.save()
            # old user but signin other social
            else:
                raise ExistEmailException

        except User.DoesNotExist:
            # new user
            user = User.objects.create(
                user_type=user_type,
                social_id=social_id,
                email=email,
                password=p_id,
                is_active=True,
                last_login=timezone.now(),
            )
            user.set_unusable_password()
            user.save()

        return user

    def extract_uid(data):
        raise NotImplementedError(
            "The provider must implement the `extract_uid()` method"
        )

    def __str__(self):
        return "social login provider"

    def __repr__(self):
        return "social login provider"


class KakaoProvider(Provider):
    id = "kakao"
    user_type = "K"

    def extract_uid(data):
        return str(data["id"])

    def extract_email(data):
        email = data["kakao_account"].get("email")
        if email is None:
            return None
        return str(email)

    def extract_nickname(data):
        nickname = data.get("properties", {}).get("nickname")
        return str(nickname)

    def extract_profile_image(data):
        profile_image = data.get("properties", {}).get("profile_image")
        return str(profile_image)


class AppleProvider(Provider):
    id = "apple"
    user_type = "A"

    def extract_uid(data):
        return str(data["sub"])

    def extract_email(data):
        return str(data["email"])
