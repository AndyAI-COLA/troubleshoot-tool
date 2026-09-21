# Troubleshoot Tool

[![Release](https://img.shields.io/github/v/release/aizhibo/troubleshoot-tool)](https://github.com/aizhibo/troubleshoot-tool/releases)
[![Docker](https://img.shields.io/badge/docker-latest-blue)](https://hub.docker.com/r/aizhibo/troubleshoot-tool)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

交互式故障排查助手 — 自动诊断服务器/网络故障，支持 Web 界面和 CLI。

> 12 个预置故障场景 · 在线诊断 · 关键词搜索 · 自定义场景 · 故障报告导出 · Docker 一键部署

## 功能特性

- 🔍 **12 个预置场景** — 服务启动失败、端口占用、连接超时、磁盘满、CPU/内存过高、SSL 证书、DNS 解析、权限不足、配置错误、防火墙拦截、服务高延迟
- ⚡ **在线诊断** — 自动执行 ping、netstat、df 等检查命令，实时反馈结果
- 🔎 **关键词搜索** — 输入关键词快速匹配故障场景和解决方案
- ✏️ **自定义场景** — 交互式创建自己的故障场景，支持数据库持久化
- 📄 **故障报告** — 一键导出 Markdown 报告（含时间线），适合发给团队
- 🖥 **Web + CLI** — Web 界面适合团队协作，CLI 适合终端操作
- 🐳 **Docker 部署** — 一键部署，含 Nginx 反向代理
- 🔒 **安全加固** — 命令白名单、非 root 运行、安全响应头

## 快速开始

### 方式一：Docker（推荐）

```bash
docker pull aizhibo/troubleshoot-tool:latest
docker run -d -p 8000:8000 --name troubleshooter aizhibo/troubleshoot-tool:latest
```

浏览器访问 `http://localhost:8000`

### 方式二：Docker Compose

```bash
git clone https://github.com/aizhibo/troubleshoot-tool.git
cd troubleshoot-tool
docker-compose up -d
```

### 方式三：pip 安装

```bash
pip install troubleshoot-tool
troubleshoot
```

### 方式四：源码运行

```bash
git clone https://github.com/aizhibo/troubleshoot-tool.git
cd troubleshoot-tool
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

## 项目结构

```
troubleshoot-tool/
├── app/                         # Web 应用（FastAPI）
│   ├── main.py                  # 入口
│   ├── api/                     # API 接口（5 个模块）
│   ├── core/                    # 核心逻辑（引擎、数据库、知识库）
│   ├── models/                  # 数据模型
│   └── static/                  # 前端（HTML/CSS/JS）
├── troubleshooter.py            # CLI 版本
├── knowledge_base.json          # 故障知识库（12 个场景）
├── Dockerfile                   # Docker 镜像（多阶段构建）
├── docker-compose.yml           # Docker Compose 编排
├── nginx.conf                   # Nginx 反向代理配置
├── pyproject.toml               # Python 项目元数据
└── requirements.txt             # Python 依赖
```

## API 文档

启动后访问 Swagger UI：`http://localhost:8000/docs`

| API | 说明 |
|-----|------|
| `GET /api/scenarios` | 获取所有场景 |
| `POST /api/scenarios` | 创建自定义场景 |
| `GET /api/search?keyword=` | 搜索知识库 |
| `POST /api/diagnosis/start` | 开始诊断 |
| `POST /api/diagnosis/{id}/run` | 执行诊断命令 |
| `GET /api/reports` | 报告列表 |
| `GET /api/history` | 历史记录 |

## 故障场景

| # | 场景 | 分类 |
|---|------|------|
| 1 | 服务启动失败 | ⚙️ 服务管理 |
| 2 | 端口占用 | 🌐 网络 |
| 3 | 连接超时 | 🌐 网络 |
| 4 | 磁盘空间不足 | 💻 系统资源 |
| 5 | CPU 使用率过高 | 💻 系统资源 |
| 6 | 内存使用率过高 | 💻 系统资源 |
| 7 | SSL/TLS 证书问题 | 🔒 安全 |
| 8 | DNS 解析失败 | 🌐 网络 |
| 9 | 权限不足 | 🔐 权限管理 |
| 10 | 配置错误 | 🔧 系统管理 |
| 11 | 防火墙拦截 | 🛡️ 网络安全 |
| 12 | 服务高延迟 | ⚡ 性能 |

编辑 `knowledge_base.json` 可添加更多场景。

## 贡献

欢迎提交 Issue 和 PR！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/my-feature`
3. 提交更改
4. 推送到分支：`git push origin feature/my-feature`
5. 创建 Pull Request

详见 [Issue 模板](.github/ISSUE_TEMPLATE/) 和 [PR 模板](.github/PULL_REQUEST_TEMPLATE.md)。

## License

[MIT](LICENSE)
