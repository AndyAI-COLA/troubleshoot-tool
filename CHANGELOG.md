# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2025-09-19

### Added
- Web 界面（FastAPI + 原生 HTML/CSS/JS）
- 12 个预置故障场景（服务管理、网络、系统资源、安全、权限、配置、防火墙、性能）
- 在线诊断功能（自动执行系统检查命令）
- 关键词搜索（匹配场景名、症状、方案、步骤）
- 自定义故障场景（交互式创建，DB 持久化）
- 历史记录管理（诊断会话列表 + 详情）
- 故障报告导出（Markdown 格式，含时间线）
- 命令执行白名单安全机制
- 响应式 UI + 深色模式自动适配
- Swagger API 文档（/docs）
- Docker 一键部署（含 Nginx 反向代理）
- GitHub Actions CI/CD 自动发布

### Changed
- CLI 版本保留，Web 版作为主要入口
- 知识库从单一 JSON 扩展为 JSON + SQLite 双源加载

### Security
- 命令白名单过滤，防止命令注入
- Docker 以非 root 用户运行
- Nginx 安全响应头（X-Content-Type-Options, X-Frame-Options 等）
- API 参数范围校验

## [1.0.0] - 2025-09-18

### Added
- CLI 交互式故障排查助手
- 8 个预置故障场景
- 彩色终端输出
- 排障日志保存（Markdown 格式）
