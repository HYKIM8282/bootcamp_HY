"""이미지4 : 검색 API 2.0 오류메시지 전체 정의"""
from rest_framework import status as http_status

VWORLD_ERROR_CODES = {
    # Level 1 : 요청 파라미터 오류
    "PARAM_REQUIRED": {
        "level": 1,
        "message": "필수 파라미터인 <%S1>가 없어서 요청을 처리할수 없습니다.",
        "http": http_status.HTTP_400_BAD_REQUEST,
    },
    "INVALID_TYPE": {
        "level": 1,
        "message": "<%S1> 파라미터 타입이 유효하지 않습니다. 유효한 타입: <%S2>, 입력값: <%S3>",
        "http": http_status.HTTP_400_BAD_REQUEST,
    },
    "INVALID_RANGE": {
        "level": 1,
        "message": "<%S1> 파라미터의 값이 유효한 범위를 넘었습니다. 유효한 타입: <%S2>, 입력값: <%S3>",
        "http": http_status.HTTP_400_BAD_REQUEST,
    },
    # Level 2 : 인증키 오류
    "INVALID_KEY": {
        "level": 2,
        "message": "등록되지 않은 인증키입니다.",
        "http": http_status.HTTP_401_UNAUTHORIZED,
    },
    "INCORRECT_KEY": {
        "level": 2,
        "message": "인증키 정보가 올바르지 않습니다. (예: 발급 시 등록 도메인이 다를 경우)",
        "http": http_status.HTTP_401_UNAUTHORIZED,
    },
    "UNAVAILABLE_KEY": {
        "level": 2,
        "message": "임시로 인증키를 사용할 수 없는 상태입니다.",
        "http": http_status.HTTP_403_FORBIDDEN,
    },
    "OVER_REQUEST_LIMIT": {
        "level": 2,
        "message": "서비스 사용량이 일일 제한량을 초과하였습니다.",
        "http": http_status.HTTP_429_TOO_MANY_REQUESTS,
    },
    # Level 3 : 시스템 오류
    "SYSTEM_ERROR": {
        "level": 3,
        "message": "시스템 에러가 발생하였습니다.",
        "http": http_status.HTTP_502_BAD_GATEWAY,
    },
    "UNKNOWN_ERROR": {
        "level": 3,
        "message": "알 수 없는 에러가 발생하였습니다.",
        "http": http_status.HTTP_502_BAD_GATEWAY,
    },
}


class VWorldAPIException(Exception):
    def __init__(self, code, raw=None):
        info = VWORLD_ERROR_CODES.get(code, VWORLD_ERROR_CODES["UNKNOWN_ERROR"])
        self.code        = code
        self.level       = info["level"]
        self.vworld_msg  = info["message"]
        self.http_status = info["http"]
        self.raw         = raw or {}
        super().__init__(self.vworld_msg)

    def to_dict(self):
        return {"error":True,"code":self.code,
                "level":self.level,"message":self.vworld_msg}


def parse_vworld_error(data):
    """응답 status가 ERROR면 에러코드 반환, 아니면 None"""
    resp = data.get("response", {})
    if resp.get("status","").upper() == "ERROR":
        return resp.get("error",{}).get("code","UNKNOWN_ERROR")
    return None