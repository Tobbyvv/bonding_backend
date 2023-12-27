from rest_framework.exceptions import APIException


class MeetingNotFoundException(APIException):
    status_code = 404
    default_detail = "해당 일정이 존재하지 않습니다."


class InvalidInviteCodeException(APIException):
    status_code = 401
    default_detail = "일정 초대 코드가 유효하지 않습니다."


class OnlyOClockAvailableException(APIException):
    status_code = 400
    default_detail = "정각만 입력 가능합니다."


class InvalidAvailableTimeException(APIException):
    status_code = 400
    default_detail = "가능한 시간 리스트가 일정의 조건에 맞지 않습니다."


class NotParticipantException(APIException):
    status_code = 403
    default_detail = "초대받지 않은 사용자입니다."


class NotAuthorException(APIException):
    status_code = 403
    default_detail = "요청 권한이 없습니다."


class ParticipantNotFoundException(APIException):
    status_code = 404
    default_detail = "참가자가 존재하지 않습니다."


class ParticipantNameExistException(APIException):
    status_code = 409
    default_detail = "닉네임 중복"
