import re
from rest_framework.status import is_client_error, is_server_error, is_success


class ResponseFormattingMiddleware:
    """
    http 응답을 처리하는 미들웨어
    """

    METHOD = ("GET", "POST", "PUT", "PATCH", "DELETE")

    def __init__(self, get_response):
        self.get_response = get_response
        # self.API_URLS = [
        #     re.compile(r'^(.*)/api'),
        #     re.compile(r'^api'),
        # ]

    def __call__(self, request):
        response = self.get_response(request)  # http응답 가져오기
        if hasattr(self, "process_response"):
            response = self.process_response(request, response)
        return response

    def process_response(self, request, response):
        """
        http 응답을 포맷팅 해주는 로직
        """

        # 미들웨어 작동 조건 검사: API_URLS, method 확인
        # path = request.path_info.lstrip("/")
        # valid_urls = (url.match(path) for url in self.API_URLS)

        # if request.method in self.METHOD and any(valid_urls):
        if request.method in self.METHOD:
            response_format = {
                "status": response.status_code,
                "success": is_success(response.status_code),
                "message": None,
                "data": {},
            }

            # response로 들어온 data 검사 및 반환
            if hasattr(response, "data") and getattr(response, "data") is not None:
                data = response.data

                try:
                    response_format["message"] = data.pop("message")
                except (KeyError, TypeError):
                    response_format.update({"data": data})
                finally:
                    response_format.pop("data")
                    if is_client_error(response.status_code):
                        message = data.pop("detail", None)  # custom API exception
                        if message:
                            response_format["message"] = message
                        else:
                            if isinstance(data, dict):
                                data = "올바른 값을 입력해주세요."
                            response_format["message"] = data
                    elif is_server_error(response.status_code):
                        response_format["message"] = "서버 내부 오류."
                    else:
                        response_format["data"] = data

                    if (
                        not response_format["success"]
                        and "data" in response_format
                        and not len(response_format["data"])
                    ):
                        response_format.pop("data")

                    response.data = response_format
                    response.content = response.render().rendered_content
            else:
                response.data = response_format

        return response
