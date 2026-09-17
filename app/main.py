from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.middleware import TraceIdMiddleware, UnhandledErrorMiddleware
from app.core.handlers import register_exception_handlers
from app.routers import api_router

app = FastAPI(
    title="FastAPI Demo",
    version="0.1.0",
    # 方案 A：不在全局改 route_class，保持显式声明
)

# ── 中间件 ──────────────────────────────────────────────────────
# add_middleware 是「前插」：每调用一次就包在新的一层外面。
# 所以下面代码的书写顺序 = 由内到外，运行时请求则是由外到内：
#
#   ServerErrorMiddleware          ← Starlette 自动加，永远在最外
#     TraceIdMiddleware            ← 分配 trace_id
#       CORSMiddleware             ← 加 access-control-*
#         UnhandledErrorMiddleware ← 兜住没被 handler 接住的异常，产出 500
#           ExceptionMiddleware    ← handlers.py 注册的那组 handler
#             Router
#
# 这个顺序是有约束的，别随手调换：
#   · 兜底中间件必须在 CORS 内层，它产出的 500 才能再穿过 CORS 带上跨域头；
#     否则浏览器看到的是跨域失败而不是 500。
#   · TraceIdMiddleware 必须在兜底中间件外层，兜底响应才能穿过它补上
#     X-Trace-Id；顺带预检 OPTIONS 也能拿到 trace_id。
app.add_middleware(UnhandledErrorMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TraceIdMiddleware)

# ── 异常处理器 ──────────────────────────────────────────────────
register_exception_handlers(app)


# ── 路由注册 ─────────────────────────────
app.include_router(api_router)
