"""知识库加载与合并逻辑。"""

import json
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_PATH = BASE_DIR / "knowledge_base.json"
CUSTOM_KB_PATH = BASE_DIR / "custom_scenarios.json"

_cache: Optional[dict] = None


def load_base_kb() -> dict:
    """加载默认知识库。"""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_custom_kb() -> dict:
    """加载用户自定义场景。"""
    if CUSTOM_KB_PATH.exists():
        try:
            with open(CUSTOM_KB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def save_custom_kb(scenarios: dict):
    """保存用户自定义场景。"""
    with open(CUSTOM_KB_PATH, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)


def get_all_scenarios() -> dict:
    """合并默认 + 自定义场景并缓存。
    自定义场景来源：JSON 文件 + SQLite 数据库。
    """
    global _cache
    if _cache is None:
        base = load_base_kb()
        custom = load_custom_kb()
        merged = dict(base.get("scenarios", {}))
        for key, val in custom.items():
            merged[f"custom_{key}"] = val

        # 合并数据库中的自定义场景
        try:
            from . import database as db
            db_customs = db.db_list_scenarios(custom_only=True)
            for sc in db_customs:
                sc_id = sc.get("id", "")
                if sc_id and f"custom_{sc_id}" not in merged:
                    merged[f"custom_{sc_id}"] = sc
        except Exception:
            pass  # DB 未初始化时忽略

        _cache = {
            "scenarios": merged,
            "categories": _merge_categories(base, custom),
            "version": base.get("version", "2.0.0"),
        }
    return _cache


def invalidate_cache():
    """场景变更后刷新缓存。"""
    global _cache
    _cache = None


def _merge_categories(base: dict, custom: dict) -> dict:
    cats = dict(base.get("categories", {}))
    # 为自定义场景中出现的新分类自动补全
    for sc in custom.values():
        cat = sc.get("category", "其他")
        if cat not in cats:
            cats[cat] = {"icon": "✏️", "color": "#e91e63"}
    cats["用户自定义"] = {"icon": "✏️", "color": "#e91e63"}
    return cats


def search_scenarios(keyword: str) -> list[dict]:
    """在知识库中搜索关键词。"""
    data = get_all_scenarios()
    keyword_lower = keyword.lower()
    results = []

    for key, sc in data["scenarios"].items():
        matches: list[str] = []
        if keyword_lower in sc.get("name", "").lower():
            matches.append(f"名称: {sc['name']}")
        if keyword_lower in sc.get("description", "").lower():
            matches.append("描述匹配")
        for symptom in sc.get("symptoms", []):
            if keyword_lower in symptom.lower():
                matches.append(f"症状: {symptom}")
        for sol in sc.get("solutions", []):
            if keyword_lower in sol.get("title", "").lower():
                matches.append(f"方案: {sol['title']}")
            for step in sol.get("steps", []):
                if keyword_lower in step.lower():
                    matches.append(f"步骤: {step}")
                    break
        if matches:
            results.append({"key": key, "scenario": sc, "matches": matches[:5]})

    return results
