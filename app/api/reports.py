"""报告导出 API。"""

import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from ..models.schemas import ReportExport
from ..core import database as db

router = APIRouter(prefix="/api/reports", tags=["报告"])


@router.get("")
def list_reports(limit: int = 50):
    """获取报告列表。"""
    limit = min(max(limit, 1), 200)
    reports = db.db_list_reports(limit)
    return {"reports": reports, "total": len(reports)}


@router.get("/{report_uuid}")
def get_report(report_uuid: str):
    """获取报告详情。"""
    report = db.db_get_report(report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


@router.get("/{report_uuid}/download")
def download_report(report_uuid: str):
    """下载报告（Markdown 文件）。"""
    report = db.db_get_report(report_uuid)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    from urllib.parse import quote
    date_part = report['exported_at'][:10]
    safe_name = f"report_{date_part}.md"
    encoded_name = f"report_{date_part}_{quote(report['scenario_name'])}.md"
    return PlainTextResponse(
        content=report["content"],
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{encoded_name}"},
    )


@router.post("/export")
def export_report(body: ReportExport):
    """从诊断会话导出报告。"""
    session = db.db_get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    now = datetime.datetime.now()
    start_str = session.get("created_at", now.isoformat())
    try:
        start_dt = datetime.datetime.fromisoformat(start_str)
        elapsed = now - start_dt
        elapsed_str = f"{int(elapsed.total_seconds())} 秒"
    except (ValueError, TypeError):
        elapsed_str = "未知"

    timeline = session.get("timeline", [])
    diag_results = session.get("diag_results", [])
    answers = session.get("answers", {})

    # 构建 Markdown 报告
    lines = [
        "# 故障排查报告",
        "",
        "| 项目 | 内容 |",
        "|------|------|",
        f"| **报告时间** | {now:%Y-%m-%d %H:%M:%S} |",
        f"| **故障场景** | {session.get('scenario_name', '未知')} |",
        f"| **排查耗时** | {elapsed_str} |",
        f"| **检查步骤数** | {len(diag_results)} |",
        "",
        "## 用户输入",
        "",
    ]
    for qid, ans in answers.items():
        lines.append(f"- **{qid}**: {ans}")
    lines.append("")

    # 时间线
    lines.append("## 诊断时间线")
    lines.append("")
    if timeline:
        lines.append("| 时间 | 阶段 | 动作 | 结果 |")
        lines.append("|------|------|------|------|")
        for event in timeline:
            if isinstance(event, dict):
                sev_icon = {"success": "✔", "warning": "▲", "error": "✘", "info": "●"}.get(
                    event.get("severity", "info"), "●"
                )
                lines.append(
                    f"| {event.get('time', '-')} | {event.get('phase', '-')} "
                    f"| {sev_icon} {event.get('action', '-')} | {event.get('result', '-')} |"
                )
    lines.append("")

    # 诊断输出
    lines.append("## 诊断结果")
    lines.append("")
    for r in diag_results:
        if isinstance(r, dict):
            status = "✔ 通过" if r.get("is_normal") else "✘ 异常"
            lines.append(f"### {r.get('description', '检查项')}")
            lines.append(f"- 命令: `{r.get('command', '')}`")
            lines.append(f"- 结果: {status} ({r.get('duration_ms', 0)}ms)")
            output = r.get("output", "") or r.get("error", "")
            if output:
                lines.append(f"```")
                lines.append(output[:2000])
                lines.append(f"```")
            lines.append("")

    if body.notes:
        lines.extend(["## 备注", "", body.notes, ""])

    lines.extend(["---", f"*由故障排查助手 Web 版 v2.0 自动生成*"])

    content = "\n".join(lines)

    # 保存报告
    report = db.db_save_report(body.session_id, session.get("scenario_name", ""), content)
    return report
