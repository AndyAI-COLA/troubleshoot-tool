"""场景 CRUD API。"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import ScenarioCreate, ScenarioUpdate
from ..core import database as db
from ..core.knowledge import get_all_scenarios, invalidate_cache

router = APIRouter(prefix="/api/scenarios", tags=["场景管理"])


@router.get("")
def list_scenarios():
    """获取所有场景（内置 + 自定义）。"""
    data = get_all_scenarios()
    result = []
    for key, sc in data["scenarios"].items():
        result.append({
            "key": key,
            "name": sc.get("name", ""),
            "category": sc.get("category", ""),
            "description": sc.get("description", ""),
            "symptoms": sc.get("symptoms", []),
            "question_count": len(sc.get("questions", [])),
            "diagnostic_count": len(sc.get("diagnostics", [])),
            "solution_count": len(sc.get("solutions", [])),
            "is_custom": key.startswith("custom_"),
        })
    return {"scenarios": result, "total": len(result)}


@router.get("/categories")
def list_categories():
    """获取所有分类。"""
    data = get_all_scenarios()
    return {"categories": data["categories"]}


@router.get("/{scenario_key}")
def get_scenario(scenario_key: str):
    """获取单个场景详情。"""
    data = get_all_scenarios()
    sc = data["scenarios"].get(scenario_key)
    if not sc:
        raise HTTPException(status_code=404, detail="场景不存在")
    return {"key": scenario_key, **sc}


@router.post("")
def create_scenario(body: ScenarioCreate):
    """创建自定义场景。"""
    record = db.db_create_scenario(body.model_dump())
    invalidate_cache()
    return record


@router.put("/{scenario_key}")
def update_scenario(scenario_key: str, body: ScenarioUpdate):
    """更新自定义场景。"""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="无更新内容")
    # DB 层 key 去掉 custom_ 前缀
    db_id = scenario_key.removeprefix("custom_")
    result = db.db_update_scenario(db_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="场景不存在或非自定义场景")
    invalidate_cache()
    return result


@router.delete("/{scenario_key}")
def delete_scenario(scenario_key: str):
    """删除自定义场景。"""
    db_id = scenario_key.removeprefix("custom_")
    ok = db.db_delete_scenario(db_id)
    if not ok:
        raise HTTPException(status_code=404, detail="场景不存在或非自定义场景")
    invalidate_cache()
    return {"deleted": True}
