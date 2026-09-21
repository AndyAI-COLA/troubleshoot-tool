#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式故障排查助手 v2.0
自动诊断常见服务器/网络故障，引导排障并记录过程。
"""

import json
import os
import platform
import re
import subprocess
import sys
import time
import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent
KB_PATH = BASE_DIR / "knowledge_base.json"
CUSTOM_KB_PATH = BASE_DIR / "custom_scenarios.json"
PROGRESS_PATH = BASE_DIR / "progress.json"


# ============================================================
#  颜色与格式化
# ============================================================

class Color:
    """ANSI 颜色码，Windows 10+ 支持。"""
    RESET   = "\033[0m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    BG_RED  = "\033[41m"
    BG_GREEN = "\033[42m"


def enable_ansi_windows():
    """在 Windows 上启用 ANSI 转义序列支持。"""
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            for attr in dir(Color):
                if attr.isupper():
                    setattr(Color, attr, "")


def colored(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"


def header(text: str, width: int = 60):
    print()
    print(colored("=" * width, Color.CYAN))
    print(colored(f"  {text}", Color.BOLD + Color.CYAN))
    print(colored("=" * width, Color.CYAN))
    print()


def sub_header(text: str):
    print()
    print(colored(f"  ── {text} ──", Color.BOLD + Color.BLUE))
    print()


def success(text: str):
    print(f"  {colored('✔', Color.GREEN)} {text}")


def error(text: str):
    print(f"  {colored('✘', Color.RED)} {text}")


def warning(text: str):
    print(f"  {colored('!', Color.YELLOW)} {text}")


def info(text: str):
    print(f"  {colored('ℹ', Color.BLUE)} {text}")


def step_hint(text: str):
    print(f"    {colored('▸', Color.DIM)} {text}")


# ============================================================
#  知识库加载
# ============================================================

def load_knowledge_base() -> dict:
    """加载默认知识库。"""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_custom_scenarios() -> dict:
    """加载用户自定义场景。"""
    if CUSTOM_KB_PATH.exists():
        try:
            with open(CUSTOM_KB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return {}
    return {}


def save_custom_scenarios(scenarios: dict):
    """保存用户自定义场景。"""
    with open(CUSTOM_KB_PATH, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)


# ============================================================
#  命令执行
# ============================================================

def run_command(command: str, timeout: int = 15) -> dict:
    """执行系统命令，返回 {success, output, error, duration_ms}。"""
    result = {"success": False, "output": "", "error": "", "duration_ms": 0}
    start = time.time()
    try:
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            startupinfo=startupinfo,
        )
        result["output"] = proc.stdout.strip()
        result["error"] = proc.stderr.strip()
        result["success"] = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result["error"] = f"命令超时（{timeout}s）"
    except Exception as e:
        result["error"] = str(e)
    result["duration_ms"] = int((time.time() - start) * 1000)
    return result


# ============================================================
#  用户交互
# ============================================================

def prompt_choice(question: str, options: list[str]) -> str:
    print()
    print(colored(f"  {question}", Color.BOLD))
    for i, opt in enumerate(options, 1):
        print(f"    {colored(str(i), Color.CYAN)}. {opt}")
    while True:
        raw = input(colored("\n  请选择 [序号]: ", Color.YELLOW)).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        error("无效输入，请输入序号。")


def prompt_text(question: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    print()
    answer = input(colored(f"  {question}{hint}\n  > ", Color.YELLOW)).strip()
    return answer if answer else default


def confirm(question: str = "继续下一步？") -> bool:
    raw = input(colored(f"\n  {question} [Y/n]: ", Color.CYAN)).strip().lower()
    return raw != "n"


def ask_save_or_quit() -> str:
    """询问用户是否保存进度并退出。"""
    print()
    options = ["保存进度并退出", "不保存直接退出", "取消，继续操作"]
    choice = prompt_choice("请选择：", options)
    return choice


# ============================================================
#  时间线记录
# ============================================================

class TimelineEvent:
    def __init__(self, phase: str, action: str, result: str = "", severity: str = "info"):
        self.time = datetime.datetime.now()
        self.phase = phase       # 阶段名: 问答 / 诊断 / 建议 / 系统
        self.action = action     # 具体动作
        self.result = result     # 结果
        self.severity = severity # info / success / warning / error

    def to_dict(self) -> dict:
        return {
            "time": self.time.strftime("%H:%M:%S"),
            "phase": self.phase,
            "action": self.action,
            "result": self.result,
            "severity": self.severity,
        }

    def display_line(self) -> str:
        ts = self.time.strftime("%H:%M:%S")
        icon_map = {
            "info": colored("●", Color.BLUE),
            "success": colored("✔", Color.GREEN),
            "warning": colored("▲", Color.YELLOW),
            "error": colored("✘", Color.RED),
        }
        icon = icon_map.get(self.severity, "●")
        line = f"  {colored(ts, Color.DIM)} {icon} [{self.phase}] {self.action}"
        if self.result:
            line += f" → {colored(self.result, Color.DIM)}"
        return line


# ============================================================
#  故障排查引擎
# ============================================================

class Troubleshooter:
    def __init__(self):
        self.kb = load_knowledge_base()
        self.custom = load_custom_scenarios()
        self.platform = "windows" if platform.system() == "Windows" else "linux"
        self.session_log: list[str] = []
        self.timeline: list[TimelineEvent] = []
        self.current_scenario_name = ""
        self.start_time = datetime.datetime.now()

        self._log(f"排障会话开始 - {self.start_time:%Y-%m-%d %H:%M:%S}")
        self._log(f"操作系统: {platform.system()} {platform.release()}")
        self._log(f"Python: {sys.version.split()[0]}")
        self._add_timeline("系统", "排障会话初始化完成")

    # ---------- 日志 ----------

    def _log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.session_log.append(f"[{ts}] {msg}")

    def _log_result(self, cmd: str, result: dict):
        status = "成功" if result["success"] else "失败"
        self._log(f"  CMD: {cmd}  → {status}")
        if result["output"]:
            for line in result["output"].splitlines()[:10]:
                self._log(f"    | {line}")

    # ---------- 时间线 ----------

    def _add_timeline(self, phase: str, action: str, result: str = "", severity: str = "info"):
        event = TimelineEvent(phase, action, result, severity)
        self.timeline.append(event)

    # ---------- 合并场景 ----------

    def _all_scenarios(self) -> dict:
        """合并默认+自定义场景。"""
        merged = dict(self.kb.get("scenarios", {}))
        for key, val in self.custom.items():
            merged[f"custom_{key}"] = val
        return merged

    def _all_categories(self) -> dict:
        """合并分类信息。"""
        cats = dict(self.kb.get("categories", {}))
        cats["用户自定义"] = {"icon": "✏️", "color": "#e91e63"}
        return cats

    # ---------- 场景展示 ----------

    def list_scenarios(self) -> list[str]:
        scenarios = self._all_scenarios()
        categories = self._all_categories()

        header("📋 故障场景列表")

        grouped: dict[str, list] = {}
        for key, sc in scenarios.items():
            cat = sc.get("category", "其他")
            grouped.setdefault(cat, []).append((key, sc))

        index = 0
        ordered_keys: list[str] = []
        for cat, items in grouped.items():
            cat_info = categories.get(cat, {})
            icon = cat_info.get("icon", "•")
            print(f"  {colored(icon, Color.BOLD)} {colored(cat, Color.BOLD)} ({len(items)} 个)")
            for key, sc in items:
                index += 1
                ordered_keys.append(key)
                custom_tag = colored(" [自定义]", Color.MAGENTA) if key.startswith("custom_") else ""
                print(f"    {colored(str(index), Color.CYAN)}. {sc['name']}{custom_tag}")
                print(f"       {colored(sc['description'][:60], Color.DIM)}")
            print()

        return ordered_keys

    # ---------- 诊断执行 ----------

    def run_diagnostics(self, scenario: dict, variables: dict) -> dict:
        """根据场景定义执行诊断命令。带进度计数器和实时反馈。"""
        results = {}
        diagnostics = scenario.get("diagnostics", [])

        # 过滤当前平台的检查
        relevant = [
            d for d in diagnostics
            if d.get("platform", "all") == "all" or d.get("platform") == self.platform
        ]

        total = len(relevant)
        sub_header(f"正在执行诊断检查 [{total} 项]")

        for idx, diag in enumerate(relevant, 1):
            # 替换变量
            cmd = diag["command"]
            for var, val in variables.items():
                cmd = cmd.replace(f"{{{var}}}", str(val))

            # 实时进度
            counter = colored(f"[{idx}/{total}]", Color.CYAN)
            print(f"\n  {counter} {colored('▸', Color.CYAN)} {diag['description']}")
            print(f"    {colored(f'$ {cmd}', Color.DIM)}")

            result = run_command(cmd)
            self._log_result(cmd, result)

            duration = f"{result['duration_ms']}ms"

            if result["success"] and result["output"]:
                is_normal = self._check_normal_output(result["output"])
                if is_normal:
                    success(f"检查通过 ({duration})")
                    self._add_timeline("诊断", diag["description"], "通过", "success")
                    for line in result["output"].splitlines()[:5]:
                        print(f"    {colored(line, Color.GREEN)}")
                else:
                    warning(f"发现问题 ({duration})")
                    self._add_timeline("诊断", diag["description"], "发现问题", "warning")
                    for line in result["output"].splitlines()[:8]:
                        print(f"    {colored(line, Color.RED)}")
            elif not result["success"] and result["error"]:
                warning(f"命令异常 ({duration}): {result['error']}")
                self._add_timeline("诊断", diag["description"], f"异常: {result['error']}", "error")
            else:
                info(f"无输出 ({duration})")
                self._add_timeline("诊断", diag["description"], "无输出", "info")

            results[diag["id"]] = result

        return results

    def _check_normal_output(self, output: str) -> bool:
        error_keywords = [
            "error", "exception", "refused", "denied", "expired",
            "failed", "not found", "no route", "timed out", "超时",
            "错误", "拒绝", "失败", "未找到", "forbidden", "forbids",
        ]
        output_lower = output.lower()
        return not any(kw in output_lower for kw in error_keywords)

    # ---------- 建议方案 ----------

    def suggest_solutions(self, scenario: dict, diag_results: dict, user_answers: dict) -> list[dict]:
        """根据诊断结果匹配并展示解决方案。返回匹配到的方案列表。"""
        solutions = scenario.get("solutions", [])
        all_output = " ".join(
            r.get("output", "") + " " + r.get("error", "")
            for r in diag_results.values()
        )
        all_output_lower = all_output.lower()
        user_text = " ".join(str(v) for v in user_answers.values()).lower()
        combined = all_output_lower + " " + user_text

        sub_header("解决方案建议")

        matched_solutions: list[dict] = []
        has_specific = False

        for sol in solutions:
            condition = sol["condition"]
            if condition == "默认":
                is_match = True
            else:
                is_match = any(
                    kw.lower() in combined
                    for kw in condition.split(" / ")
                )

            if is_match:
                if condition == "默认" and has_specific:
                    continue
                if condition != "默认":
                    has_specific = True
                matched_solutions.append(sol)

        for sol in matched_solutions:
            print(f"\n  {colored('■', Color.GREEN)} {colored(sol['title'], Color.BOLD)}")
            for i, step in enumerate(sol["steps"], 1):
                print(f"    {colored(str(i) + '.', Color.CYAN)} {step}")
            self._log(f"建议方案: {sol['title']}")
            self._add_timeline("建议", sol["title"], f"{len(sol['steps'])} 步", "success")

        if not matched_solutions:
            warning("未能匹配到具体方案，请根据上方诊断结果手动分析。")
            self._add_timeline("建议", "未匹配到方案", "", "warning")

        return matched_solutions

    # ---------- 搜索功能 ----------

    def _search_flow(self):
        """搜索知识库中的故障场景。"""
        header("🔍 搜索故障问题")

        keyword = prompt_text("请输入关键词（如：端口、内存、证书、DNS 等）：")
        if not keyword:
            return

        keyword_lower = keyword.lower()
        scenarios = self._all_scenarios()

        results: list[tuple[str, dict, list[str]]] = []
        for key, sc in scenarios.items():
            matches: list[str] = []
            # 匹配名称
            if keyword_lower in sc.get("name", "").lower():
                matches.append(f"名称: {sc['name']}")
            # 匹配描述
            if keyword_lower in sc.get("description", "").lower():
                matches.append(f"描述匹配")
            # 匹配症状
            for symptom in sc.get("symptoms", []):
                if keyword_lower in symptom.lower():
                    matches.append(f"症状: {symptom}")
            # 匹配解决方案
            for sol in sc.get("solutions", []):
                if keyword_lower in sol.get("title", "").lower():
                    matches.append(f"方案: {sol['title']}")
                for step in sol.get("steps", []):
                    if keyword_lower in step.lower():
                        matches.append(f"步骤: {step}")
                        break

            if matches:
                results.append((key, sc, matches))

        if not results:
            info(f"未找到与 '{keyword}' 相关的场景。")
            return

        print()
        print(f"  找到 {colored(str(len(results)), Color.CYAN)} 个相关场景：\n")

        ordered_keys: list[str] = []
        for idx, (key, sc, matches) in enumerate(results, 1):
            ordered_keys.append(key)
            print(f"  {colored(str(idx), Color.CYAN)}. {colored(sc['name'], Color.BOLD)}")
            for m in matches[:3]:
                print(f"     {colored('•', Color.DIM)} {colored(m, Color.DIM)}")
            print()

        if confirm("是否进入某个场景排查？"):
            raw = prompt_text(f"输入序号 [1-{len(ordered_keys)}]：")
            if raw.isdigit() and 1 <= int(raw) <= len(ordered_keys):
                key = ordered_keys[int(raw) - 1]
                self._run_scenario(key, self._all_scenarios()[key])

    # ---------- 自定义场景 ----------

    def _custom_scenario_flow(self):
        """交互式创建自定义故障场景。"""
        header("✏️  创建自定义故障场景")

        name = prompt_text("场景名称（如：Redis 连接异常）：")
        if not name:
            return

        categories = list(self._all_categories().keys())
        category = prompt_choice("选择分类：", categories + ["新建分类"])
        if category == "新建分类":
            category = prompt_text("输入新分类名称：")

        description = prompt_text("场景描述：", default=name)

        # 症状
        symptoms: list[str] = []
        print(colored("\n  输入常见症状（每行一条，输入空行结束）：", Color.BOLD))
        while True:
            s = input(colored("    症状 > ", Color.YELLOW)).strip()
            if not s:
                break
            symptoms.append(s)

        if not symptoms:
            symptoms = [description]

        # 诊断命令
        diagnostics: list[dict] = []
        print(colored("\n  添加诊断命令（每条需要：描述、命令、平台）", Color.BOLD))
        print(colored("  平台选项: all / windows / linux", Color.DIM))
        idx = 1
        while True:
            print(colored(f"\n  ── 诊断命令 #{idx} ──", Color.DIM))
            desc = input(colored("    描述（空行结束）> ", Color.YELLOW)).strip()
            if not desc:
                break
            cmd = input(colored("    命令 > ", Color.YELLOW)).strip()
            if not cmd:
                break
            plat = input(colored("    平台 [all]: ", Color.YELLOW)).strip() or "all"
            diagnostics.append({
                "id": f"custom_check_{idx}",
                "command": cmd,
                "description": desc,
                "platform": plat,
            })
            idx += 1

        # 解决方案
        solutions: list[dict] = []
        print(colored("\n  添加解决方案（每条需要：标题、匹配条件、步骤）", Color.BOLD))
        print(colored("  条件: 关键词/关键词 用 / 分隔，输入 '默认' 作为兜底方案", Color.DIM))
        while True:
            print(colored("\n  ── 解决方案 ──", Color.DIM))
            title = input(colored("    标题（空行结束）> ", Color.YELLOW)).strip()
            if not title:
                break
            condition = input(colored("    匹配条件 [默认]: ", Color.YELLOW)).strip() or "默认"
            steps: list[str] = []
            print(colored("    输入解决步骤（空行结束）：", Color.DIM))
            while True:
                step = input(colored("    步骤 > ", Color.YELLOW)).strip()
                if not step:
                    break
                steps.append(step)
            if steps:
                solutions.append({
                    "title": title,
                    "condition": condition,
                    "steps": steps,
                })

        if not confirm(f"\n  确认保存场景「{name}」？"):
            return

        scenario_key = re.sub(r'[^a-z0-9_]', '_', name.lower().replace(' ', '_'))
        new_scenario = {
            "name": name,
            "category": category,
            "description": description,
            "symptoms": symptoms,
            "questions": [
                {"id": "q1", "text": "请描述具体错误信息或现象：", "type": "text"}
            ],
            "diagnostics": diagnostics,
            "solutions": solutions,
        }

        self.custom[scenario_key] = new_scenario
        save_custom_scenarios(self.custom)
        success(f"自定义场景「{name}」已保存！")
        self._add_timeline("系统", f"创建自定义场景: {name}", "成功", "success")

    # ---------- 导出报告 ----------

    def export_report(self, extra_info: str = "") -> Optional[Path]:
        """生成 Markdown 格式的故障报告。"""
        header("📄 导出故障报告")

        if not self.timeline:
            warning("当前没有排障记录可导出。")
            return None

        report_dir = BASE_DIR / "reports"
        report_dir.mkdir(exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        scenario_tag = re.sub(r'[^a-zA-Z0-9_]', '_', self.current_scenario_name) if self.current_scenario_name else "general"
        filename = f"report_{ts}_{scenario_tag}.md"
        filepath = report_dir / filename

        # 构建报告
        lines = []
        lines.append(f"# 故障排查报告")
        lines.append("")
        lines.append(f"| 项目 | 内容 |")
        lines.append(f"|------|------|")
        lines.append(f"| **报告时间** | {datetime.datetime.now():%Y-%m-%d %H:%M:%S} |")
        lines.append(f"| **故障场景** | {self.current_scenario_name or '快速检查'} |")
        lines.append(f"| **操作系统** | {platform.system()} {platform.release()} |")
        lines.append(f"| **Python 版本** | {sys.version.split()[0]} |")
        lines.append(f"| **排查耗时** | {self._elapsed()} |")
        lines.append(f"| **检查步骤数** | {len(self.timeline)} |")

        # 统计
        successes = sum(1 for t in self.timeline if t.severity == "success")
        warnings = sum(1 for t in self.timeline if t.severity == "warning")
        errors = sum(1 for t in self.timeline if t.severity == "error")
        lines.append(f"| **正常/警告/异常** | {successes} / {warnings} / {errors} |")
        lines.append("")

        # 时间线
        lines.append("## 排障时间线")
        lines.append("")
        lines.append("| 时间 | 阶段 | 动作 | 结果 |")
        lines.append("|------|------|------|------|")
        for event in self.timeline:
            severity_icon = {"success": "✔", "warning": "▲", "error": "✘", "info": "●"}.get(event.severity, "●")
            result_text = event.result.replace("|", "\\|") if event.result else "-"
            action_text = event.action.replace("|", "\\|")
            lines.append(f"| {event.time:%H:%M:%S} | {event.phase} | {severity_icon} {action_text} | {result_text} |")
        lines.append("")

        # 完整日志
        lines.append("## 详细日志")
        lines.append("")
        lines.append("```")
        for entry in self.session_log:
            lines.append(entry)
        lines.append("```")
        lines.append("")

        if extra_info:
            lines.append("## 备注")
            lines.append("")
            lines.append(extra_info)
            lines.append("")

        lines.append("---")
        lines.append(f"*由交互式故障排查助手 v2.0 自动生成 | {datetime.datetime.now():%Y-%m-%d %H:%M:%S}*")

        filepath.write_text("\n".join(lines), encoding="utf-8")
        success(f"报告已导出: {filepath}")
        self._add_timeline("系统", f"导出报告: {filename}", "成功", "success")
        return filepath

    def _elapsed(self) -> str:
        delta = datetime.datetime.now() - self.start_time
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds} 秒"
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes} 分 {seconds} 秒"

    # ---------- 时间线展示 ----------

    def _show_timeline(self):
        """展示排障时间线。"""
        if not self.timeline:
            return

        sub_header("排障时间线")
        for event in self.timeline:
            print(event.display_line())
        print()

    # ---------- 进度保存 / 恢复 ----------

    def _save_progress(self, state: dict):
        """保存排障进度。"""
        state["_saved_at"] = datetime.datetime.now().isoformat()
        state["_session_log"] = self.session_log
        state["_timeline"] = [t.to_dict() for t in self.timeline]
        state["_scenario_name"] = self.current_scenario_name
        state["_start_time"] = self.start_time.isoformat()
        PROGRESS_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_progress(self) -> Optional[dict]:
        """加载上次未完成的进度。"""
        if not PROGRESS_PATH.exists():
            return None
        try:
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, KeyError):
            return None

    def _clear_progress(self):
        """清除进度文件。"""
        if PROGRESS_PATH.exists():
            PROGRESS_PATH.unlink()

    def _restore_session_from_progress(self, state: dict):
        """从进度恢复会话状态。"""
        self.session_log = state.get("_session_log", [])
        self.current_scenario_name = state.get("_scenario_name", "")
        start_str = state.get("_start_time")
        if start_str:
            try:
                self.start_time = datetime.datetime.fromisoformat(start_str)
            except (ValueError, TypeError):
                self.start_time = datetime.datetime.now()
        # 恢复时间线
        self.timeline = []
        for td in state.get("_timeline", []):
            evt = TimelineEvent(td.get("phase", ""), td.get("action", ""), td.get("result", ""), td.get("severity", "info"))
            try:
                evt.time = datetime.datetime.strptime(
                    f"{datetime.datetime.now():%Y-%m-%d} {td['time']}", "%Y-%m-%d %H:%M:%S"
                )
            except (ValueError, KeyError):
                evt.time = datetime.datetime.now()
            self.timeline.append(evt)

    def _resume_flow(self):
        """继续上次未完成的排障。"""
        state = self._load_progress()
        if not state:
            info("没有找到未完成的进度。")
            return

        self._restore_session_from_progress(state)
        scenario_key = state.get("scenario_key", "")
        all_scenarios = self._all_scenarios()

        if scenario_key not in all_scenarios:
            error(f"上次的场景 '{state.get('_scenario_name', '')}' 已不存在。")
            self._clear_progress()
            return

        scenario = all_scenarios[scenario_key]
        completed = state.get("completed_steps", [])
        variables = state.get("variables", {})
        diag_results = state.get("diag_results", {})

        header(f"♻️  继续排障: {scenario['name']}")
        info(f"上次进度: {', '.join(completed) if completed else '刚开始'}")

        # 判断需要继续的步骤
        if "diagnostics" not in completed:
            # 需要运行诊断
            if not variables:
                # 补充提问
                for q in scenario.get("questions", []):
                    if q["id"] not in variables:
                        if q["type"] == "choice":
                            answer = prompt_choice(q["text"], q["options"])
                        else:
                            answer = prompt_text(q["text"])
                        variables[q["id"]] = answer
                        self._log(f"  Q: {q['text']}")
                        self._log(f"  A: {answer}")

                extracted = self._extract_variables(variables)
                variables.update(extracted)

            diag_results = self.run_diagnostics(scenario, variables)
            completed.append("diagnostics")

            self._save_progress({
                "scenario_key": scenario_key,
                "completed_steps": completed,
                "variables": variables,
                "diag_results": diag_results,
            })

        if "solutions" not in completed:
            self.suggest_solutions(scenario, diag_results, variables)
            completed.append("solutions")

        self._show_timeline()
        self._clear_progress()
        success("排障已完成！")

    # ---------- 快速检查 ----------

    def quick_check(self):
        """不选择场景，直接运行一组通用健康检查。"""
        header("🔍 快速系统健康检查")
        self.current_scenario_name = "快速检查"
        self._add_timeline("系统", "开始快速健康检查")

        checks = [
            ("磁盘空间", "df -h" if self.platform == "linux"
             else "wmic logicaldisk get size,freespace,caption"),
            ("内存使用", "free -h" if self.platform == "linux"
             else 'powershell -Command "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory | Format-List"'),
            ("网络连通性", "ping -c 2 8.8.8.8" if self.platform == "linux"
             else "ping -n 2 8.8.8.8"),
            ("DNS 解析", "dig google.com +short || nslookup google.com" if self.platform == "linux"
             else "nslookup google.com"),
            ("活跃监听端口", "ss -tlnp 2>/dev/null || netstat -tlnp" if self.platform == "linux"
             else "netstat -ano | findstr LISTENING"),
            ("系统负载", "uptime" if self.platform == "linux"
             else "powershell -Command \"(Get-CimInstance Win32_Processor | Measure-Object LoadPercentage).Average\""),
        ]

        total = len(checks)
        for idx, (name, cmd) in enumerate(checks, 1):
            counter = colored(f"[{idx}/{total}]", Color.CYAN)
            print(f"\n  {counter} {colored('▸', Color.CYAN)} {name}")
            result = run_command(cmd)
            self._log_result(cmd, result)
            if result["success"] and result["output"]:
                is_normal = self._check_normal_output(result["output"])
                severity = "success" if is_normal else "warning"
                self._add_timeline("诊断", name, "通过" if is_normal else "有问题", severity)
                lines = result["output"].splitlines()[:6]
                for line in lines:
                    color = Color.GREEN
                    low = line.lower()
                    if any(k in low for k in ["error", "fail", "denied", "refused"]):
                        color = Color.RED
                    print(f"    {colored(line, color)}")
            elif result["error"]:
                print(f"    {colored(result['error'], Color.RED)}")
                self._add_timeline("诊断", name, f"异常: {result['error']}", "error")
            else:
                self._add_timeline("诊断", name, "无输出", "info")

        self._show_timeline()

        # 自动导出
        if confirm("是否导出健康检查报告？"):
            self.export_report()

        self._clear_progress()

    # ---------- 使用引导 ----------

    def _show_tutorial(self):
        """展示使用引导。"""
        header("📖 使用引导 - 交互式故障排查助手 v2.0")
        guides = [
            ("选择故障场景排查",
             "从预置的 12 个故障场景中选择，程序会通过交互问答引导你描述问题，\n"
             "    自动执行诊断命令，并给出针对性解决方案。"),
            ("搜索故障问题",
             "输入关键词搜索知识库，快速定位相关故障场景和解决方案。\n"
             "    支持搜索场景名、症状、方案等所有内容。"),
            ("快速系统健康检查",
             "一键运行磁盘、内存、网络、DNS、端口、负载等通用检查，\n"
             "    快速了解系统整体状态。"),
            ("自定义故障场景",
             "交互式创建你自己的故障场景，包括症状、诊断命令和解决方案，\n"
             "    自动保存，下次可直接使用。"),
            ("导出故障报告",
             "将排障过程导出为 Markdown 格式报告，包含时间线和完整日志，\n"
             "    适合发送给开发团队或记录存档。"),
            ("进度保存",
             "排障过程中如果中断（Ctrl+C 或选择退出），会自动保存进度，\n"
             "    下次启动可选择继续未完成的排查。"),
            ("键盘操作提示",
             "所有选择题输入数字序号；文本输入直接打字；\n"
             "    输入 'back' 可返回上一层；'Ctrl+C' 可中断当前操作。"),
        ]

        for title, desc in guides:
            print(f"  {colored('▸', Color.CYAN)} {colored(title, Color.BOLD)}")
            for line in desc.split('\n'):
                print(f"    {colored(line.strip(), Color.DIM)}")
            print()

        print(colored("  ─────────────────────────────────────────────", Color.DIM))
        info(f"知识库: {len(self.kb.get('scenarios', {}))} 个预置场景 + {len(self.custom)} 个自定义场景")
        info("编辑 knowledge_base.json 可添加预置场景")
        info("自定义场景通过菜单中的「自定义故障场景」创建")
        print()
        confirm("了解完毕，按回车返回主菜单。")

    # ---------- 展示知识库 ----------

    def _show_knowledge_base(self):
        header("📚 故障知识库")

        scenarios = self._all_scenarios()
        categories = self._all_categories()
        grouped: dict[str, list] = {}
        for key, sc in scenarios.items():
            cat = sc.get("category", "其他")
            grouped.setdefault(cat, []).append((key, sc))

        for cat, items in grouped.items():
            cat_info = categories.get(cat, {})
            icon = cat_info.get("icon", "•")
            print(f"  {icon} {colored(cat, Color.BOLD)} ({len(items)} 个场景)")
            for key, sc in items:
                tag = colored(" [自定义]", Color.MAGENTA) if key.startswith("custom_") else ""
                print(f"    • {sc['name']}{tag}: {sc['description'][:55]}")
            print()

        total_default = len(self.kb.get("scenarios", {}))
        total_custom = len(self.custom)
        info(f"共 {total_default} 个预置场景 + {total_custom} 个自定义场景")
        print()
        confirm("按回车返回主菜单。")

    # ---------- 变量提取 ----------

    def _extract_variables(self, user_answers: dict[str, str]) -> dict[str, str]:
        extracted = {}
        all_text = " ".join(str(v) for v in user_answers.values())

        port_match = re.search(r'(?:(?:端口|port)[:\s]*)?(\d{2,5})', all_text)
        if port_match:
            extracted["port"] = port_match.group(1)

        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', all_text)
        if ip_match:
            extracted["target"] = ip_match.group(1)

        if not ip_match:
            domain_match = re.search(
                r'([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)',
                all_text
            )
            if domain_match:
                extracted["target"] = domain_match.group(1)

        if "service_name" not in extracted:
            for key, val in user_answers.items():
                val_str = str(val).strip()
                if val_str and len(val_str) < 50 and not val_str.isdigit():
                    extracted["service_name"] = val_str
                    break

        return extracted

    # ---------- 单场景执行（供搜索/恢复复用） ----------

    def _run_scenario(self, scenario_key: str, scenario: dict):
        """完整的场景排障流程，支持进度保存。"""
        self.current_scenario_name = scenario["name"]

        header(f"🛠  排查: {scenario['name']}")
        info(scenario["description"])

        # 展示症状
        print(colored("  常见症状：", Color.BOLD))
        for symptom in scenario.get("symptoms", []):
            print(f"    • {symptom}")

        if not confirm("\n  是否开始交互式排查？"):
            return

        self._log(f"\n=== 开始排查: {scenario['name']} ===")
        self._add_timeline("问答", f"开始排查: {scenario['name']}")

        # 交互问答
        variables: dict[str, str] = {}
        for q in scenario.get("questions", []):
            if q["type"] == "choice":
                answer = prompt_choice(q["text"], q["options"])
            else:
                answer = prompt_text(q["text"])

            variables[q["id"]] = answer
            self._log(f"  Q: {q['text']}")
            self._log(f"  A: {answer}")
            self._add_timeline("问答", q["text"], answer[:40])

        # 保存进度：问答完成
        self._save_progress({
            "scenario_key": scenario_key,
            "completed_steps": ["questions"],
            "variables": variables,
            "diag_results": {},
        })

        extracted = self._extract_variables(variables)
        variables.update(extracted)

        # 运行诊断
        self._add_timeline("诊断", "开始执行诊断检查")
        diag_results = self.run_diagnostics(scenario, variables)

        # 保存进度：诊断完成
        self._save_progress({
            "scenario_key": scenario_key,
            "completed_steps": ["questions", "diagnostics"],
            "variables": variables,
            "diag_results": diag_results,
        })

        # 展示建议
        self.suggest_solutions(scenario, diag_results, variables)

        # 时间线
        self._show_timeline()

        # 导出报告
        print()
        extra = prompt_text("（可选）备注信息，直接回车跳过：")
        if extra:
            self._add_timeline("系统", f"备注: {extra[:40]}")

        if confirm("是否导出故障报告（Markdown 格式）？"):
            self.export_report(extra)

        self._clear_progress()

    # ---------- 主流程 ----------

    def run(self):
        enable_ansi_windows()

        # 首次运行引导检测
        if not (BASE_DIR / "logs").exists() and not (BASE_DIR / "reports").exists():
            self._print_banner()
            self._show_tutorial()
        else:
            self._print_banner()

        while True:
            self._main_menu()

    def _print_banner(self):
        banner = r"""
  ╔══════════════════════════════════════════════════════╗
  ║       🔧 交互式故障排查助手 v2.0  🔧                ║
  ║       Troubleshooting Assistant                      ║
  ║       搜索 · 排查 · 报告 · 自定义                    ║
  ╚══════════════════════════════════════════════════════╝
"""
        print(colored(banner, Color.CYAN))

    def _main_menu(self):
        has_progress = self._load_progress() is not None

        if has_progress:
            options = [
                "选择故障场景排查",
                "搜索故障问题",
                "快速系统健康检查",
                "自定义故障场景",
                "查看知识库",
                "导出故障报告",
                "继续上次未完成的排障",
                "使用引导",
                "退出",
            ]
        else:
            options = [
                "选择故障场景排查",
                "搜索故障问题",
                "快速系统健康检查",
                "自定义故障场景",
                "查看知识库",
                "导出故障报告",
                "使用引导",
                "退出",
            ]

        choice = prompt_choice("请选择操作：", options)

        if choice == options[0]:
            self._scenario_menu()
        elif choice == options[1]:
            self._search_flow()
        elif choice == options[2]:
            self.quick_check()
        elif choice == options[3]:
            self._custom_scenario_flow()
        elif choice == options[4]:
            self._show_knowledge_base()
        elif choice == options[5]:
            self.export_report()
        elif "继续" in choice:
            self._resume_flow()
        elif "引导" in choice:
            self._show_tutorial()
        else:
            self._exit_flow()

    def _scenario_menu(self):
        """场景选择与排查。"""
        ordered_keys = self.list_scenarios()
        if not ordered_keys:
            error("知识库中没有可用场景。")
            return

        idx = prompt_text("请输入故障场景序号（或 'back' 返回）：")
        if idx.lower() == "back":
            return

        if not idx.isdigit() or not (1 <= int(idx) <= len(ordered_keys)):
            error("无效序号。")
            return

        scenario_key = ordered_keys[int(idx) - 1]
        scenario = self._all_scenarios()[scenario_key]
        self._run_scenario(scenario_key, scenario)

    def _exit_flow(self):
        """退出流程，询问是否保存进度。"""
        if self.timeline:
            print()
            choice = ask_save_or_quit()
            if choice.startswith("保存"):
                self._save_progress({
                    "scenario_key": "",
                    "completed_steps": [],
                    "variables": {},
                    "diag_results": {},
                })
                success("进度已保存，下次启动可选择「继续上次排障」。")
            elif choice.startswith("不"):
                self._clear_progress()
            else:
                return  # 取消退出

        print()
        info("再见！祝排障顺利 👋")
        print()
        sys.exit(0)


# ============================================================
#  入口
# ============================================================

def main():
    try:
        ts = Troubleshooter()
        ts.run()
    except KeyboardInterrupt:
        print()
        info("用户中断。")
        # 尝试保存进度
        try:
            ts._save_progress({
                "scenario_key": "",
                "completed_steps": [],
                "variables": {},
                "diag_results": {},
            })
            success("进度已自动保存，下次启动可继续。")
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
