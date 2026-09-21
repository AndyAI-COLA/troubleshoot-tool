"""排障引擎 — 从 CLI 版本重构，供 API 调用。"""

import platform
import re
import subprocess
import time
import datetime
from typing import Optional


# ── 命令执行 ──

# 命令白名单前缀（安全限制）
ALLOWED_CMD_PREFIXES = [
    "netstat", "ss", "ping", "nslookup", "dig", "tracert", "traceroute",
    "tracepath", "df", "du", "free", "uptime", "top", "ps", "lsof",
    "whoami", "id", "set", "env", "cat", "ls", "find", "head", "tail",
    "wc", "uname", "hostname", "ipconfig", "tasklist", "taskkill",
    "wmic", "netsh", "nft", "iptables", "ufw", "firewall-cmd",
    "echo", "powershell", "systemctl", "service", "docker", "certbot",
    "openssl", "curl", "wget",
]


def is_command_allowed(cmd: str) -> bool:
    """检查命令是否在白名单中。"""
    first_token = cmd.strip().split()[0].lower() if cmd.strip() else ""
    # 允许管道组合命令（简单检查每个段）
    segments = [s.strip().split()[0].lower() for s in cmd.split("|") if s.strip()]
    return all(
        any(seg.startswith(prefix) for prefix in ALLOWED_CMD_PREFIXES)
        for seg in segments
    )


def run_command(command: str, timeout: int = 15) -> dict:
    """执行系统命令，返回 {success, output, error, duration_ms}。
    执行前检查命令白名单，不在白名单中的命令会被拒绝。
    """
    if not is_command_allowed(command):
        return {"success": False, "output": "", "error": "命令不在白名单中，出于安全考虑已被拒绝", "duration_ms": 0}
    result = {"success": False, "output": "", "error": "", "duration_ms": 0}
    start = time.time()
    try:
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, startupinfo=startupinfo,
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


# ── 变量提取 ──

def extract_variables(user_answers: dict) -> dict:
    """从用户回答中自动提取端口、IP、域名、服务名等。"""
    extracted = {}
    all_text = " ".join(str(v) for v in user_answers.values())

    port_match = re.search(r'(?:(?:端口|port)[:\s]*)?(\d{2,5})', all_text)
    if port_match:
        extracted["port"] = port_match.group(1)

    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', all_text)
    if ip_match:
        extracted["target"] = ip_match.group(1)
    else:
        domain_match = re.search(
            r'([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)',
            all_text,
        )
        if domain_match:
            extracted["target"] = domain_match.group(1)

    for key, val in user_answers.items():
        val_str = str(val).strip()
        if val_str and len(val_str) < 50 and not val_str.isdigit():
            extracted.setdefault("service_name", val_str)
            break

    return extracted


# ── 诊断执行 ──

def run_diagnostics(scenario: dict, variables: dict, platform_name: str = "linux") -> list[dict]:
    """
    执行场景定义的诊断命令，返回结构化结果列表。
    每项: {id, description, command, output, error, success, duration_ms, is_normal}
    """
    diagnostics = scenario.get("diagnostics", [])
    results = []

    for diag in diagnostics:
        diag_platform = diag.get("platform", "all")
        if diag_platform != "all" and diag_platform != platform_name:
            continue

        cmd = diag["command"]
        for var, val in variables.items():
            cmd = cmd.replace(f"{{{var}}}", str(val))

        result = run_command(cmd)
        result["id"] = diag["id"]
        result["description"] = diag["description"]
        result["command"] = cmd
        result["is_normal"] = _check_normal_output(result.get("output", "") + " " + result.get("error", ""))
        results.append(result)

    return results


def _check_normal_output(output: str) -> bool:
    error_keywords = [
        "error", "exception", "refused", "denied", "expired",
        "failed", "not found", "no route", "timed out", "超时",
        "错误", "拒绝", "失败", "未找到", "forbidden",
    ]
    output_lower = output.lower()
    return not any(kw in output_lower for kw in error_keywords)


# ── 方案匹配 ──

def match_solutions(scenario: dict, diag_results: list[dict], user_answers: dict) -> list[dict]:
    """根据诊断结果和用户回答匹配解决方案。"""
    solutions = scenario.get("solutions", [])
    all_output = " ".join(
        r.get("output", "") + " " + r.get("error", "")
        for r in diag_results
    )
    user_text = " ".join(str(v) for v in user_answers.values()).lower()
    combined = all_output.lower() + " " + user_text

    matched: list[dict] = []
    has_specific = False

    for sol in solutions:
        condition = sol.get("condition", "默认")
        if condition == "默认":
            is_match = True
        else:
            is_match = any(kw.lower() in combined for kw in condition.split(" / "))

        if is_match:
            if condition == "默认" and has_specific:
                continue
            if condition != "默认":
                has_specific = True
            matched.append({
                "title": sol["title"],
                "steps": sol["steps"],
                "condition": condition,
            })

    return matched


# ── 平台检测 ──

def get_platform() -> str:
    return "windows" if platform.system() == "Windows" else "linux"
