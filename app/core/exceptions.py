from enum import IntEnum

from fastapi import HTTPException


class ErrorCode(IntEnum):

    # 通用 / 参数
    VALIDATION_ERROR = 20001
    # 认证
    UNAUTHORIZED = 40100
    LOGIN_FAILED = 40101
    # 权限
    FORBIDDEN = 40300
    # 资源
    NOT_FOUND = 40400
    CONFLICT = 40900               # 用户已存在等
    # 服务
    INTERNAL_ERROR = 50000

class BizError(HTTPException):
    def __init__(
            self, 
            code: ErrorCode | int,
            message: str,
            http_status: int = 400,
            headers: dict | None = None
    ) -> None:
        super().__init__(status_code=http_status, detail=message, headers=headers)
        self.biz_code = int(code)
        self.biz_message = message

    

