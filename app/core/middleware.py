import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.trace import bind_trace_id, trace_id_var


class TraceIdMiddleware(BaseHTTPMiddleware):
    """给每个请求分配 trace_id，并回写 X-Trace-Id 响应头。

    注册在中间件栈的最外层（见 main.py 的顺序说明）。放在最外层是必须的：
    内层兜底中间件产出的 500 响应要穿过这里，才能带上 X-Trace-Id。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tid = uuid.uuid4().hex[:12]
        token = bind_trace_id(request, tid)

        try:
            response: Response = await call_next(request)
            response.headers["X-Trace-Id"] = tid
            return response
        finally:
            trace_id_var.reset(token)


class UnhandledErrorMiddleware(BaseHTTPMiddleware):
    """兜住所有没被 exception_handler 接住的异常，转成统一的 500。

    ★ 必须夹在 CORSMiddleware 的**内层**。

    没被 handler 接住的异常最终会由 Starlette 的 ServerErrorMiddleware 处理，
    而它位于整个栈的最外层、在 CORSMiddleware 之外 —— 它生成的响应不经过 CORS，
    浏览器只会报跨域失败，真正的 500 根本看不到（实测 access-control-allow-origin
    会缺失，排查方向直接被带偏）。在这里兜住，响应就还能正常穿过 CORS 带回头。

    handlers.py 里仍保留 Exception 处理器作为最后兜底（例如异常发生在 CORS 自身）。
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # 延迟导入：handlers 依赖 trace，顶层导入会绕回来
            from app.core.handlers import render_internal_error

            return render_internal_error(request, exc)
