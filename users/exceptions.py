from rest_framework.exceptions import APIException


class InvalidTokenException(APIException):
    status_code = 401
    default_detail = "유효하지 않은 토큰 값입니다."

    def __init__(self, error=None, detail=None, code=None):
        if error is not None:
            detail = error
        super().__init__(detail, code)


class SkipTokenException(APIException):
    status_code = 401
    default_detail = "리프레시 토큰이 필요합니다."


class SocialException(APIException):
    pass


class SocialDataException(SocialException):
    status_code = 500
    default_detail = "정보를 불러올 수 없습니다."


class ExistEmailException(APIException):
    status_code = 409
    default_detail = "이미 가입되어 있는 이메일입니다."
