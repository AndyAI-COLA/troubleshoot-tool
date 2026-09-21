"""历史记录 API。"""

from fastapi import APIRouter, HTTPException
from ..core import database as db

router = APIRouter(prefix="/api/history", tags=["历史记录"])


@router.get("")
def list_history(status: str = "", limit: int = 50):
    """获取诊断历史记录。"""
    limit = min(max(limit, 1), 200)
    sessions = db.db_list_sessions(status=status or None, limit=limit)
    # 精简返回，不含完整 diag_results
    result = []
    for s in sessions:
        result.append({
            "id": s.get("id", ""),
            "scenario_id": s.get("scenario_id", ""),
            "scenario_name": s.get("scenario_name", ""),
            "status": s.get("status", ""),
            "created_at": s.get("created_at", ""),
            "completed_at": s.get("completed_at", ""),
            "answers": s.get("answers", {}),
        })
    return {"history": result, "total": len(result)}


@router.get("/{session_id}")
def get_history_detail(session_id: str):
    """获取单条历史记录详情。"""
    session = db.db_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="记录不存在")
    return session
