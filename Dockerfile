# ── Stage 1: Builder ──
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──
FROM python:3.11-slim AS runtime

# OCI 镜像元数据
LABEL org.opencontainers.image.title="troubleshoot-tool"
LABEL org.opencontainers.image.description="交互式故障排查助手 — 自动诊断服务器/网络故障"
LABEL org.opencontainers.image.source="https://github.com/aizhibo/troubleshoot-tool"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# 复制依赖
COPY --from=builder /install /usr/local

# 复制应用
COPY app/ app/
COPY knowledge_base.json .
COPY custom_scenarios.json* ./

# 创建数据目录和非 root 用户
RUN mkdir -p data reports && \
    groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
