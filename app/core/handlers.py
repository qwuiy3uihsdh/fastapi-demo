import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.exceptions import BizError, ErrorCode
from app.core.trace import current_trace_id

logger = logging.getLogger("app")


def _body(
    request: Request,
    code: int,
    msg: str,
    http_status: int,
    extra: dict | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "message": msg,
            "data": extra,          # 字段错误放这；正常错误时 None
            "trace_id": current_trace_id(request),
        },
    )


def render_internal_error(request: Request, exc: Exception) -> JSONResponse:
    """未捕获异常的兜底响应。服务器日志记全堆栈，对外不泄露细节。

    UnhandledErrorMiddleware 和下面的 Exception 处理器共用这一份，
    保证两条路径的响应体完全一致。
    """
    logger.exception("Unhandled exception", exc_info=exc)
    return _body(request, ErrorCode.INTERNAL_ERROR, "服务内部错误", 500)


def register_exception_handlers(app: FastAPI) -> None:

    # ── 1. 业务异常 BizError ─────────────────────────────────────
    @app.exception_handler(BizError)
    async def biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.biz_code,
                "message": exc.biz_message,
                "data": None,
                "trace_id": current_trace_id(request),
            },
            headers=exc.headers or {},
        )

    # ── 2. Starlette / FastAPI HTTPException（含 401/403/404）────
    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # ★ 关键：保留 WWW-Authenticate，Swagger Authorize 才弹窗
        headers = dict(exc.headers or {})
        code = {
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
        }.get(exc.status_code, exc.status_code * 100)  # 兜底用 http*100

        resp = JSONResponse(
            status_code=exc.status_code,
            content={
                "code": int(code),
                "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                "data": None,
                "trace_id": current_trace_id(request),
            },
        )
        for k, v in headers.items():
            resp.headers[k] = v
        return resp

    # ── 3. 入参校验失败 (422) ────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # 精简字段错误：[{loc: ["body","email"], msg: "field required"}]
        errors = [
            {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return _body(request, ErrorCode.VALIDATION_ERROR, "参数校验失败", 422, extra={"errors": errors})

    # ── 4. 出参校验失败 ──────────────────────────────────────────
    @app.exception_handler(ResponseValidationError)
    async def response_validation_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
        logger.error("Response validation error: %s", exc.errors(), exc_info=False)
        return _body(request, ErrorCode.INTERNAL_ERROR, "服务出参异常，请联系后端", 500)

    # ── 5. 最后兜底（正常路径由 UnhandledErrorMiddleware 接住）────
    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return render_internal_error(request, exc)
