"""Pydantic 数据模型。"""

from pydantic import BaseModel, Field
from typing import Optional


# ── 场景 ──

class QuestionModel(BaseModel):
    id: str
    text: str
    type: str = "text"
    options: list[str] = []


class DiagnosticModel(BaseModel):
    id: str
    command: str
    description: str
    platform: str = "all"


class SolutionStep(BaseModel):
    title: str
    condition: str = "默认"
    steps: list[str] = []


class ScenarioCreate(BaseModel):
    name: str
    category: str = ""
    description: str = ""
    symptoms: list[str] = []
    questions: list[QuestionModel] = []
    diagnostics: list[DiagnosticModel] = []
    solutions: list[SolutionStep] = []


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    symptoms: Optional[list[str]] = None
    questions: Optional[list[QuestionModel]] = None
    diagnostics: Optional[list[DiagnosticModel]] = None
    solutions: Optional[list[SolutionStep]] = None


# ── 诊断 ──

class DiagnosisAnswer(BaseModel):
    question_id: str
    answer: str


class DiagnosisStart(BaseModel):
    scenario_id: str


# ── 搜索 ──

class SearchRequest(BaseModel):
    keyword: str


# ── 报告 ──

class ReportExport(BaseModel):
    session_id: str
    notes: str = ""
