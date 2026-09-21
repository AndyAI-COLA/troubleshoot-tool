"""搜索 API。"""

from fastapi import APIRouter
from ..core.knowledge import search_scenarios

router = APIRouter(prefix="/api/search", tags=["搜索"])


@router.get("")
def search(keyword: str = ""):
    """搜索故障场景。"""
    if not keyword.strip():
        return {"results": [], "total": 0, "keyword": keyword}
    results = search_scenarios(keyword.strip())
    return {"results": results, "total": len(results), "keyword": keyword}
