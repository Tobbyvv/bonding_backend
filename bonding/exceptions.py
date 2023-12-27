from rest_framework.exceptions import APIException


class NotFoundException(APIException):
    status_code = 404
    default_detail = "찾을 수 없습니다."


class UnprocessableEntityException(APIException):
    status_code = 422
    default_detail = "파라미터가 누락되었거나 값이 유효하지 않습니다."


class EmptyTimeException(APIException):
    status_code = 400
    default_detail = "시간이 최소 한 개 존재해야 합니다."


class StartTimeIsEqualOrLaterThanEndTimeException(APIException):
    status_code = 400
    default_detail = "시작 시간이 종료 시간과 같거나 종료 시간보다 앞섭니다."


class StartTimeIsLaterThanEndTimeException(APIException):
    status_code = 400
    default_detail = "시작 시간이 종료 시간보다 앞섭니다."


class UnAvailableTimeException(APIException):
    status_code = 400
    default_detail = "입력 시간이 올바르지 않습니다."


class ServerException(APIException):
    status_code = 500
    default_code = "서버 내부 오류."
