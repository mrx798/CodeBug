"""
Task 3 — Security Fix (Hard)
Agent receives code with a hidden security vulnerability.
Must: (1) identify the vulnerability type, (2) fix the code, (3) explain why dangerous.
Grader: 0.4*vuln_found + 0.4*code_fixed + 0.2*explanation_quality
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from models import Action, BugEntry, BugType, Reward, TaskInfo, VulnerabilityType
from corpus.bug_corpus import get_bugs_by_type
from reward import compute_security_reward


TASK_ID = "security_fix"
_TIMEOUT = 10


class SecurityFixTask:
    task_id: str = TASK_ID

    @staticmethod
    def info() -> TaskInfo:
        return TaskInfo(
            task_id=TASK_ID,
            name="Security Fix",
            difficulty="hard",
            description=(
                "Agent receives code with a hidden security vulnerability — SQL injection, "
                "hardcoded API keys, unsafe eval(), path traversal, or insecure deserialization. "
                "Agent must identify the vulnerability type, fix the code, and explain why it was dangerous."
            ),
            target_score="~0.30 (GPT-4o)",
            num_test_cases=3,
            max_steps=5,
        )

    @staticmethod
    def get_bugs() -> list[BugEntry]:
        return get_bugs_by_type(BugType.SECURITY)

    @staticmethod
    def check_vulnerability_identified(action: Action, entry: BugEntry) -> bool:
        """Check if the agent correctly identified the vulnerability type."""
        if entry.vulnerability_type is None:
            return False
        expl = action.bug_explanation.lower()
        vuln_keywords: dict[str, list[str]] = {
            "sql_injection": ["sql injection", "sql", "inject", "parameterized", "prepared statement"],
            "hardcoded_secret": ["hardcoded", "hard-coded", "secret", "credential", "api key", "password in code"],
            "unsafe_eval": ["eval", "exec", "code injection", "arbitrary code", "code execution"],
            "path_traversal": ["path traversal", "directory traversal", "../", "traversal", "realpath"],
            "insecure_deserialization": ["deserialization", "pickle", "yaml.load", "unsafe load", "serialize"],
            "command_injection": ["command injection", "os.system", "shell injection", "shell=true", "subprocess"],
        }
        keywords = vuln_keywords.get(entry.vulnerability_type.value, [])
        return any(kw in expl for kw in keywords)

    @staticmethod
    def check_code_fixed(action: Action, entry: BugEntry) -> bool:
        """Run bandit on the fixed code to check if vulnerabilities are resolved."""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(action.fixed_code)
                f.flush()
                tmp_path = f.name

            result = subprocess.run(
                [sys.executable, "-m", "bandit", "-q", "-ll", tmp_path],
                capture_output=True, text=True, timeout=_TIMEOUT,
            )
            # If bandit finds no high-severity issues, the code is "fixed"
            no_issues = result.returncode == 0 or "No issues" in result.stdout
            
            # Also check that the fixed code doesn't contain the original vulnerability patterns
            code_lower = action.fixed_code.lower()
            if entry.vulnerability_type == VulnerabilityType.SQL_INJECTION:
                # Check for string formatting in SQL
                has_vuln = ("f\"select" in code_lower or "f'select" in code_lower or
                            "format(" in code_lower and "select" in code_lower or
                            ("+ " in code_lower and "select" in code_lower and "'" in code_lower))
                return no_issues or not has_vuln
            elif entry.vulnerability_type == VulnerabilityType.HARDCODED_SECRET:
                # Check for hardcoded strings that look like secrets
                suspicious = ["sk-", "password", "secret", "key-", "token"]
                has_secret = any(s in code_lower for s in suspicious if 
                               s in code_lower and "environ" not in code_lower.split(s)[0][-50:])
                return "os.environ" in code_lower or "getenv" in code_lower
            elif entry.vulnerability_type == VulnerabilityType.UNSAFE_EVAL:
                return "eval(" not in action.fixed_code and "exec(" not in action.fixed_code
            elif entry.vulnerability_type == VulnerabilityType.PATH_TRAVERSAL:
                return "realpath" in code_lower or "basename" in code_lower
            elif entry.vulnerability_type == VulnerabilityType.INSECURE_DESERIALIZATION:
                return "pickle.loads" not in action.fixed_code and "yaml.load(" not in action.fixed_code.replace("safe_load", "")
            elif entry.vulnerability_type == VulnerabilityType.COMMAND_INJECTION:
                return "shell=True" not in action.fixed_code and "os.system" not in action.fixed_code
            return no_issues
        except Exception:
            return False
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass

    @staticmethod
    def compute_explanation_quality(action: Action, entry: BugEntry) -> float:
        """Score explanation by matching against known security concepts."""
        if not entry.security_concepts:
            return 0.0
        expl = action.bug_explanation.lower()
        hits = sum(1 for concept in entry.security_concepts if concept.lower() in expl)
        return min(hits / max(len(entry.security_concepts), 1), 1.0)

    @staticmethod
    def grade(action: Action, entry: BugEntry, previous_best: float = 0.0) -> Reward:
        vuln_found = SecurityFixTask.check_vulnerability_identified(action, entry)
        code_fixed = SecurityFixTask.check_code_fixed(action, entry)
        expl_quality = SecurityFixTask.compute_explanation_quality(action, entry)
        return compute_security_reward(
            action, entry,
            vuln_found=vuln_found,
            code_fixed=code_fixed,
            explanation_quality=expl_quality,
            previous_best=previous_best,
        )

    @staticmethod
    def grade_score(action: Action, entry: BugEntry) -> tuple[float, dict[str, Any]]:
        """Pure grader: score = 0.4*vuln + 0.4*fix + 0.2*explanation."""
        vuln_found = SecurityFixTask.check_vulnerability_identified(action, entry)
        code_fixed = SecurityFixTask.check_code_fixed(action, entry)
        expl_quality = SecurityFixTask.compute_explanation_quality(action, entry)

        score = 0.4 * float(vuln_found) + 0.4 * float(code_fixed) + 0.2 * expl_quality
        return round(score, 4), {
            "vulnerability_found": vuln_found,
            "code_fixed": code_fixed,
            "explanation_quality": round(expl_quality, 4),
        }
