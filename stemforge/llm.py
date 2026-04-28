"""StemForge — LLM abstraction layer.

Provides a unified interface for language model calls with two implementations:
  - OpenAILLM : uses the OpenAI API (requires OPENAI_API_KEY)
  - MockLLM   : deterministic mock for testing without an API key

The factory function ``get_llm()`` selects the implementation automatically.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Dict, List

from stemforge.models import Finding


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class BaseLLM(ABC):
    """Abstract interface every LLM backend must implement."""

    @abstractmethod
    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Send prompts to the LLM and return a raw JSON string."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""
        ...


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------

class OpenAILLM(BaseLLM):
    """Calls the OpenAI Chat Completions API."""

    def __init__(self, model: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package required. Run: pip install openai")
        self.client = OpenAI()  # reads OPENAI_API_KEY from env
        self.model = model

    def call(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or "{}"

    def name(self) -> str:
        return f"OpenAI ({self.model})"


# ---------------------------------------------------------------------------
# Mock implementation
# ---------------------------------------------------------------------------

class MockLLM(BaseLLM):
    """Deterministic mock LLM for offline testing.

    Two detection modes:
      * **Baseline** — only catches the three most obvious patterns
        (hardcoded_secret, debug_enabled, insecure_eval).
      * **Evolved** — comprehensive pattern matching when the system
        prompt contains a security checklist.
    """

    # Baseline: intentionally limited detection
    BASELINE_RULES: Dict[str, List[str]] = {
        "hardcoded_secret": [
            r'(?:SECRET_KEY|API_KEY|PASSWORD)\s*=\s*["\']',
        ],
        "debug_enabled": [
            r'debug\s*=\s*True',
        ],
        "insecure_eval": [
            r'\beval\s*\(',
        ],
    }

    # Evolved: comprehensive detection
    EVOLVED_RULES: Dict[str, List[str]] = {
        "sql_injection": [
            r'f["\'].*SELECT.*\{',
            r'SELECT.*\+\s*\w+',
            r'cursor\.execute\(.*f["\']',
            r'cursor\.execute\(.*\+',
        ],
        "hardcoded_secret": [
            r'(?:SECRET_KEY|API_KEY|PASSWORD|TOKEN|PRIVATE_KEY)\s*=\s*["\']',
        ],
        "command_injection": [
            r'os\.system\s*\(',
            r'os\.popen\s*\(',
            r'subprocess\..*shell\s*=\s*True',
        ],
        "path_traversal": [
            r'open\s*\(.*(?:request|user|filename|path)',
            r'send_file\s*\(.*(?:request|filename|filepath)',
            r'request\.args\.get\s*\(\s*["\'](?:file|path)',
        ],
        "insecure_eval": [
            r'\beval\s*\(',
            r'\bexec\s*\(',
        ],
        "weak_password_hash": [
            r'hashlib\.md5\s*\(',
            r'hashlib\.sha1\s*\(',
        ],
        "debug_enabled": [
            r'debug\s*=\s*True',
        ],
        "open_redirect": [
            r'redirect\s*\(\s*(?:next_url|url|request\.args)',
        ],
        "insecure_deserialization": [
            r'pickle\.loads?\s*\(',
            r'yaml\.(?:load|unsafe_load)\s*\(',
        ],
    }

    SEVERITY: Dict[str, str] = {
        "sql_injection": "high",
        "hardcoded_secret": "high",
        "command_injection": "critical",
        "path_traversal": "high",
        "insecure_eval": "critical",
        "weak_password_hash": "medium",
        "debug_enabled": "low",
        "open_redirect": "medium",
        "insecure_deserialization": "critical",
    }

    FIX: Dict[str, str] = {
        "sql_injection": "Use parameterized queries instead of string formatting.",
        "hardcoded_secret": "Move secrets to environment variables or a secrets manager.",
        "command_injection": "Use subprocess with a list of arguments; avoid shell=True.",
        "path_traversal": "Validate and sanitize file paths; use an allowlist.",
        "insecure_eval": "Avoid eval/exec; use ast.literal_eval or a safe parser.",
        "weak_password_hash": "Use bcrypt, scrypt, or argon2 for password hashing.",
        "debug_enabled": "Disable debug mode in production.",
        "open_redirect": "Validate redirect URLs against an allowlist of trusted domains.",
        "insecure_deserialization": "Avoid deserializing untrusted data; use JSON instead of pickle.",
    }

    # ---- public interface --------------------------------------------------

    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Return a JSON string containing detected findings."""
        code = user_prompt
        filename = self._guess_filename(user_prompt)
        rules = self._select_rules(system_prompt)
        findings = self._detect(code, rules, filename)
        return json.dumps({"findings": [f.model_dump() for f in findings]}, indent=2)

    def name(self) -> str:
        return "MockLLM (deterministic)"

    # ---- internals ---------------------------------------------------------

    def _select_rules(self, system_prompt: str) -> Dict[str, List[str]]:
        """Choose baseline or evolved rules based on prompt content."""
        prompt_lower = system_prompt.lower()
        indicators = [
            "sql_injection", "command_injection", "path_traversal",
            "open_redirect", "insecure_deserialization", "checklist",
            "security review specialist", "vulnerability classes",
        ]
        if sum(1 for kw in indicators if kw in prompt_lower) >= 2:
            return self.EVOLVED_RULES
        return self.BASELINE_RULES

    def _detect(self, code: str, rules: Dict[str, List[str]], filename: str) -> List[Finding]:
        findings: List[Finding] = []
        for vuln_type, patterns in rules.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                    evidence = self._extract_evidence(code, pattern)
                    findings.append(Finding(
                        type=vuln_type,
                        severity=self.SEVERITY.get(vuln_type, "medium"),
                        file=filename,
                        evidence=evidence,
                        fix=self.FIX.get(vuln_type, "Review and fix the issue."),
                    ))
                    break  # one finding per vuln type per file
        return findings

    @staticmethod
    def _extract_evidence(code: str, pattern: str) -> str:
        for line in code.split("\n"):
            if re.search(pattern, line, re.IGNORECASE):
                return line.strip()
        return "Pattern match detected."

    @staticmethod
    def _guess_filename(prompt: str) -> str:
        """Try to extract a filename hint from the user prompt."""
        m = re.search(r'file:\s*(\S+\.py)', prompt, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r'(\w+\.py)', prompt)
        if m:
            return m.group(1)
        return "unknown.py"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_llm() -> BaseLLM:
    """Return the appropriate LLM backend based on environment."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key and api_key != "your-api-key-here":
        return OpenAILLM()
    return MockLLM()
