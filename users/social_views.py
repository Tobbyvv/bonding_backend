import requests
import time
import jwt as pyjwt
from authlib.jose import jwt
from teampang.settings import base as settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from teampang.exceptions import UnprocessableEntityException
from .jwt_auth import get_tokens_for_user
from .provider import KakaoProvider, AppleProvider
from .exceptions import InvalidTokenException


class SocialLoginView(GenericAPIView):
    permission_classes = (AllowAny,)

    def complete_login(self, request):
        try:
            """
            1. 소셜 로그인에 필요한 정보를 얻는 요청보내기
            2. profile_json에 직렬화한 유저 정보 담기
            """
            pass

        except Exception:
            raise InvalidTokenException

        return self.provider.sociallogin(
            {
                "email": "test@example.com",
                "id": "123115545",
            }
        )

    def get_response(self, user):
        data = get_tokens_for_user(user)
        data.update({"message": "로그인 성공"})

        return Response(data, status=status.HTTP_200_OK)

    def expire_socialtoken(self, request):
        """
        소셜앱에서 회원 정보를 요청하는 데 사용한 토큰 만료
        """
        pass

    def post(self, request, *args, **kwargs):
        user = self.complete_login(request)
        self.expire_socialtoken(request)
        return self.get_response(user)


class KakaoLoginView(SocialLoginView):
    provider = KakaoProvider
    profile_url = "https://kapi.kakao.com/v2/user/me"

    def complete_login(self, request):
        try:
            access_token = request.data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            profile_request = requests.post(
                self.profile_url,
                headers=headers,
            )
            profile_json = profile_request.json()
        except Exception:
            raise InvalidTokenException
        return self.provider.sociallogin(profile_json)


class AppleLoginView(SocialLoginView):
    provider = AppleProvider
    profile_url = "https://appleid.apple.com/auth/token"

    def get_client_id_and_secret(self):
        with open(settings.SOCIAL_AUTH_APPLE_PRIVATE_KEY_PATH, "rb") as f:
            private_key = f.read()

        header = {
            "kid": settings.SOCIAL_AUTH_APPLE_KEY_ID,
            "alg": "ES256",
        }
        payload = {
            "iss": settings.SOCIAL_AUTH_APPLE_TEAM_ID,
            "iat": int(time.time()),
            "exp": int(time.time()) + 60 * 60,
            "aud": "https://appleid.apple.com",
            "sub": settings.SOCIAL_AUTH_APPLE_CLIENT_ID,
        }
        client_secret = jwt.encode(
            header=header,
            payload=payload,
            key=private_key,
        ).decode("utf-8")

        return settings.SOCIAL_AUTH_APPLE_CLIENT_ID, client_secret

    def complete_login(self, request):
        try:
            client_id, client_secret = self.get_client_id_and_secret()
            authorization_code = request.data["authorization_code"]
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": authorization_code,
                "grant_type": "authorization_code",
                "redirect_uri": "https://example.com/redirect",
            }
            response = requests.post(
                url=self.profile_url,
                data=data,
                headers=headers,
            )
            response_dict = response.json()

            # check response data has id_token
            id_token = response_dict["id_token"]
            decoded = pyjwt.decode(id_token, options={"verify_signature": False})

        except Exception:
            raise InvalidTokenException

        # check decoded data validate
        if (
            decoded["iss"] == "https://appleid.apple.com"
            and decoded["aud"] == client_id
        ):
            return self.provider.sociallogin(decoded)
        else:
            raise InvalidTokenException


class KaKaoDisconnectView(GenericAPIView):
    diconnect_url = "https://kapi.kakao.com/v1/user/unlink"

    def get_key():
        return settings.secrets["KAKAO"]["ADMIN_KEY"]

    def disconnect(self, user):
        key = self.get_key()
        try:
            headers = {
                "Authorization": f"KakaoAK {key}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = {
                "target_id": int(user.social_id),
                "target_id_type": "user_id",
            }
            requests.post(self.diconnect_url, data=data, headers=headers)
        except Exception:
            raise UnprocessableEntityException
