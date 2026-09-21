"""SQLite 数据库初始化与基础操作。"""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "troubleshooter.db"


def _ensure_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_db():
    """初始化数据库表。"""
    _ensure_dir()
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                description TEXT DEFAULT '',
                symptoms TEXT DEFAULT '[]',
                questions TEXT DEFAULT '[]',
                diagnostics TEXT DEFAULT '[]',
                solutions TEXT DEFAULT '[]',
                is_custom INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS diagnosis_sessions (
                id TEXT PRIMARY KEY,
                scenario_id TEXT,
                scenario_name TEXT DEFAULT '',
                status TEXT DEFAULT 'in_progress',
                answers TEXT DEFAULT '{}',
                variables TEXT DEFAULT '{}',
                diag_results TEXT DEFAULT '{}',
                timeline TEXT DEFAULT '[]',
                session_log TEXT DEFAULT '[]',
                created_at TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS reports (
                uuid TEXT PRIMARY KEY,
                session_id TEXT,
                scenario_name TEXT DEFAULT '',
                content TEXT DEFAULT '',
                exported_at TEXT
            );
        """)


@contextmanager
def _get_conn():
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── 场景 CRUD ──

def db_list_scenarios(custom_only: bool = False) -> list[dict]:
    with _get_conn() as conn:
        if custom_only:
            rows = conn.execute(
                "SELECT * FROM scenarios WHERE is_custom=1 ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM scenarios ORDER BY is_custom, created_at DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def db_get_scenario(scenario_id: str) -> Optional[dict]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM scenarios WHERE id=?", (scenario_id,)).fetchone()
    return _row_to_dict(row) if row else None


def db_create_scenario(data: dict) -> dict:
    now = datetime.now().isoformat()
    sid = data.get("id") or f"custom_{uuid.uuid4().hex[:8]}"
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO scenarios (id,name,category,description,symptoms,questions,
               diagnostics,solutions,is_custom,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                data["name"],
                data.get("category", ""),
                data.get("description", ""),
                json.dumps(data.get("symptoms", []), ensure_ascii=False),
                json.dumps(data.get("questions", []), ensure_ascii=False),
                json.dumps(data.get("diagnostics", []), ensure_ascii=False),
                json.dumps(data.get("solutions", []), ensure_ascii=False),
                1,
                now,
                now,
            ),
        )
    return db_get_scenario(sid)


def db_update_scenario(scenario_id: str, data: dict) -> Optional[dict]:
    existing = db_get_scenario(scenario_id)
    if not existing:
        return None
    now = datetime.now().isoformat()
    fields = {
        "name": data.get("name", existing["name"]),
        "category": data.get("category", existing["category"]),
        "description": data.get("description", existing["description"]),
        "symptoms": json.dumps(data.get("symptoms", existing["symptoms"]), ensure_ascii=False),
        "questions": json.dumps(data.get("questions", existing["questions"]), ensure_ascii=False),
        "diagnostics": json.dumps(data.get("diagnostics", existing["diagnostics"]), ensure_ascii=False),
        "solutions": json.dumps(data.get("solutions", existing["solutions"]), ensure_ascii=False),
        "updated_at": now,
    }
    set_clause = ", ".join(f"{k}=?" for k in fields)
    with _get_conn() as conn:
        conn.execute(f"UPDATE scenarios SET {set_clause} WHERE id=?", (*fields.values(), scenario_id))
    return db_get_scenario(scenario_id)


def db_delete_scenario(scenario_id: str) -> bool:
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM scenarios WHERE id=?", (scenario_id,))
    return cur.rowcount > 0


# ── 诊断会话 ──

def db_create_session(scenario_id: str, scenario_name: str) -> dict:
    sid = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO diagnosis_sessions
               (id,scenario_id,scenario_name,status,created_at)
               VALUES (?,?,?,?,?)""",
            (sid, scenario_id, scenario_name, "in_progress", now),
        )
    return {"id": sid, "scenario_id": scenario_id, "scenario_name": scenario_name,
            "status": "in_progress", "created_at": now}


def db_update_session(session_id: str, **kwargs):
    allowed = {"status", "answers", "variables", "diag_results", "timeline", "session_log", "completed_at"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    # 序列化 JSON 字段
    for k in ("answers", "variables", "diag_results", "timeline", "session_log"):
        if k in updates and not isinstance(updates[k], str):
            updates[k] = json.dumps(updates[k], ensure_ascii=False)
    set_clause = ", ".join(f"{k}=?" for k in updates)
    with _get_conn() as conn:
        conn.execute(f"UPDATE diagnosis_sessions SET {set_clause} WHERE id=?",
                     (*updates.values(), session_id))


def db_get_session(session_id: str) -> Optional[dict]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM diagnosis_sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    for k in ("answers", "variables", "diag_results", "timeline", "session_log"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def db_list_sessions(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    with _get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM diagnosis_sessions WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM diagnosis_sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        for k in ("answers", "variables", "diag_results", "timeline", "session_log"):
            if d.get(k):
                try:
                    d[k] = json.loads(d[k])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(d)
    return results


# ── 报告 ──

def db_save_report(session_id: str, scenario_name: str, content: str) -> dict:
    rpt_uuid = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO reports (uuid,session_id,scenario_name,content,exported_at) VALUES (?,?,?,?,?)",
            (rpt_uuid, session_id, scenario_name, content, now),
        )
    return {"uuid": rpt_uuid, "session_id": session_id, "scenario_name": scenario_name,
            "exported_at": now}


def db_get_report(rpt_uuid: str) -> Optional[dict]:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM reports WHERE uuid=?", (rpt_uuid,)).fetchone()
    return dict(row) if row else None


def db_list_reports(limit: int = 50) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT uuid,session_id,scenario_name,exported_at FROM reports ORDER BY exported_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── 辅助 ──

def _row_to_dict(row) -> dict:
    d = dict(row)
    for k in ("symptoms", "questions", "diagnostics", "solutions"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
