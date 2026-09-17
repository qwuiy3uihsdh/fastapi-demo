

from typing import Any

from pydantic import BaseModel, Field

from app.core.trace import current_trace_id


class ApiResponse[T](BaseModel):
    code: int = Field(default=0, description="业务码,0=成功")
    message: str = Field(default="ok")
    data: T | None = Field(default=None)
    trace_id: str | None = Field(default=None)

    @classmethod
    def ok(cls, data: Any = None, message: str = "ok", trace_id: str | None = None) -> dict:
        return {
            "code": 0,
            "message": message,
            "data": data,
            # 与错误响应保持一致：默认取当前请求的 trace_id
            # 这里拿不到 Request 对象，走 contextvar 分支
            "trace_id": trace_id or current_trace_id() or None,
        }