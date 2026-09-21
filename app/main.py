"""FastAPI 入口。"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import time as _time

from .core.database import init_db
from .api import scenarios, diagnosis, search, reports, history

# ── 日志配置 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("troubleshooter")

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="故障排查助手",
    description="交互式故障排查 Web 版 — 在线诊断 · 知识库管理 · 报告导出",
    version="2.0.0",
)

# ── CORS 中间件 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 请求日志中间件 ──
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = _time.time()
    response = await call_next(request)
    duration_ms = int((_time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response

# ── 注册路由 ──
app.include_router(scenarios.router)
app.include_router(diagnosis.router)
app.include_router(search.router)
app.include_router(reports.router)
app.include_router(history.router)

# ── 静态文件 ──
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
