from rest_framework.exceptions import APIException


class ProfileDoesNotExistException(APIException):
    status_code = 404
    default_detail = "프로필이 없는 사용자입니다."


class NicknameConflictException(APIException):
    status_code = 409
    default_detail = "이미 사용중인 닉네임입니다."


class ProfileConflictException(APIException):
    status_code = 422
    default_detail = "이미 프로필이 존재하는 사용자입니다."


class NicknameParameterException(APIException):
    status_code = 422
    default_detail = "조회하실 회원의 닉네임을 입력해주세요."


class ScheduleConflictException(APIException):
    status_code = 409
    default_detail = "입력한 시간 범위에 이미 일정이 존재합니다."


class OnlyFiveMinuteAvailableException(APIException):
    status_code = 400
    default_detail = "5분 단위만 입력 가능합니다."
