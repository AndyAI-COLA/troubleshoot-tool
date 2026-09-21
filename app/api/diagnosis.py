"""在线诊断 API。"""

import datetime
from fastapi import APIRouter, HTTPException
from ..models.schemas import DiagnosisStart, DiagnosisAnswer
from ..core import database as db
from ..core import engine
from ..core.knowledge import get_all_scenarios

router = APIRouter(prefix="/api/diagnosis", tags=["在线诊断"])


@router.post("/start")
def start_diagnosis(body: DiagnosisStart):
    """开始一次诊断会话。"""
    data = get_all_scenarios()
    scenario = data["scenarios"].get(body.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    session = db.db_create_session(body.scenario_id, scenario["name"])
    return {
        "session_id": session["id"],
        "scenario": {
            "name": scenario["name"],
            "description": scenario.get("description", ""),
            "symptoms": scenario.get("symptoms", []),
            "questions": scenario.get("questions", []),
        },
    }


@router.post("/{session_id}/answer")
def submit_answer(session_id: str, body: DiagnosisAnswer):
    """提交一个问答答案。"""
    session = db.db_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    answers = session.get("answers", {})
    answers[body.question_id] = body.answer
    db.db_update_session(session_id, answers=answers)

    # 检查是否所有问题都已回答
    data = get_all_scenarios()
    scenario = data["scenarios"].get(session.get("scenario_id", ""), {})
    questions = scenario.get("questions", [])
    all_answered = all(q["id"] in answers for q in questions)

    return {
        "question_id": body.question_id,
        "answers": answers,
        "all_answered": all_answered,
        "total_questions": len(questions),
        "answered_questions": len(answers),
    }


@router.post("/{session_id}/run")
def run_diagnosis(session_id: str):
    """执行诊断命令，返回结果。"""
    session = db.db_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    data = get_all_scenarios()
    scenario = data["scenarios"].get(session.get("scenario_id", ""), {})
    if not scenario:
        raise HTTPException(status_code=404, detail="场景数据丢失")

    answers = session.get("answers", {})
    # 合并自动提取的变量
    variables = engine.extract_variables(answers)
    variables.update(answers)

    platform_name = engine.get_platform()
    diag_results = engine.run_diagnostics(scenario, variables, platform_name)

    # 保存诊断结果
    db.db_update_session(
        session_id,
        variables=variables,
        diag_results=diag_results,
        status="diagnosed",
    )

    return {
        "session_id": session_id,
        "variables": variables,
        "results": diag_results,
        "platform": platform_name,
    }


@router.post("/{session_id}/suggest")
def get_suggestions(session_id: str):
    """获取解决方案建议。"""
    session = db.db_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    data = get_all_scenarios()
    scenario = data["scenarios"].get(session.get("scenario_id", ""), {})
    diag_results = session.get("diag_results", [])
    answers = session.get("answers", {})

    if isinstance(diag_results, str):
        import json
        diag_results = json.loads(diag_results)

    solutions = engine.match_solutions(scenario, diag_results, answers)

    # 标记完成
    db.db_update_session(
        session_id,
        status="completed",
        completed_at=datetime.datetime.now().isoformat(),
    )

    return {
        "session_id": session_id,
        "solutions": solutions,
        "scenario_name": session.get("scenario_name", ""),
    }


@router.get("/{session_id}")
def get_session(session_id: str):
    """获取诊断会话详情。"""
    session = db.db_get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session
