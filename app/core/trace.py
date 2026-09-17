"""trace_id 的唯一读写入口。

为什么要有两个存储位置：

- ``trace_id_var`` (ContextVar)：视图/服务层拿不到 Request 对象时用，
  ``ApiResponse.ok()`` 就靠它。contextvar 会随 context 复制进 anyio 线程池，
  所以同步 def 端点里读也是有效的。
- ``request.state``：``request.state`` 背后是 ``scope["state"]``，全程同一个 dict，
  **中间件退出后依然可读**。走到了 TCP 兜底 handler 的异常，contextvar 已经被
  reset 成默认值了，这时只能靠它。

读取一律走 :func:`current_trace_id`，别自己 ``.get()``。
"""

from contextvars import ContextVar

from starlette.requests import Request

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

# request.state 上的属性名
STATE_KEY = "trace_id"


def bind_trace_id(request: Request, tid: str) -> object:
    """绑定 trace_id，返回给 contextvar 用于稍后 reset 的 token。"""
    setattr(request.state, STATE_KEY, tid)
    return trace_id_var.set(tid)


def current_trace_id(request: Request | None = None) -> str:
    """取当前请求的 trace_id。

    优先 request.state（生命周期覆盖整个请求，含最外层异常处理器），
    没有 request 对象或还没绑定时回退到 contextvar。
    """
    if request is not None:
        tid = getattr(request.state, STATE_KEY, "")
        if tid:
            return tid
    return trace_id_var.get()
