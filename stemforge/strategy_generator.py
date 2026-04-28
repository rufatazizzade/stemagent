"""StemForge — Strategy Generator.

Takes a DomainProfile and produces a specialist Strategy including
a checklist, output format, and analysis approach.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from stemforge.llm import BaseLLM
from stemforge.models import DomainProfile, Strategy, EvaluationResult


class StrategyGenerator:
    """Creates a specialist strategy from a domain profile."""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def generate(
        self,
        profile: DomainProfile,
        previous_result: EvaluationResult | None = None,
        iteration: int = 1,
    ) -> Strategy:
        """Generate a specialist strategy.

        Parameters
        ----------
        profile : DomainProfile
            Domain profile to base the strategy on.
        previous_result : EvaluationResult, optional
            Results from the previous iteration for refinement.
        iteration : int
            Current iteration number.

        Returns
        -------
        Strategy
        """
        try:
            return self._llm_generate(profile, previous_result, iteration)
        except Exception:
            return self._deterministic_generate(profile)

    # ------------------------------------------------------------------
    # LLM-based generation
    # ------------------------------------------------------------------

    def _llm_generate(
        self,
        profile: DomainProfile,
        previous_result: EvaluationResult | None,
        iteration: int,
    ) -> Strategy:
        feedback = ""
        if previous_result and iteration > 1:
            missed = []
            for fname, detail in previous_result.details.items():
                if detail.get("fn", 0) > 0:
                    expected = detail.get("expected", [])
                    detected = detail.get("detected", [])
                    missed.extend(set(expected) - set(detected))
            if missed:
                feedback = (
                    f"\n\nPrevious iteration missed these vulnerability types: "
                    f"{', '.join(missed)}. Make sure the checklist includes them."
                )

        system = (
            "You are a specialist strategy architect. Given a domain profile, "
            "produce a JSON strategy with these keys:\n"
            "  - checklist: list of vulnerability types to check, using EXACT "
            "snake_case labels like: sql_injection, hardcoded_secret, "
            "command_injection, path_traversal, insecure_eval, "
            "weak_password_hash, debug_enabled, open_redirect, "
            "insecure_deserialization\n"
            "  - output_format: dict describing the expected output schema\n"
            "  - analysis_approach: string describing how to analyze code\n"
            "  - severity_levels: list of severity levels\n"
            "IMPORTANT: Use snake_case for all checklist items. "
            "Do NOT use human-readable names like 'SQL Injection'. "
            "Use machine labels like 'sql_injection'."
            f"{feedback}"
        )
        user = f"Domain profile:\n{profile.model_dump_json(indent=2)}"
        raw = self.llm.call(system, user)
        data = self._parse_json(raw)
        return Strategy(**data)

    # ------------------------------------------------------------------
    # Deterministic fallback
    # ------------------------------------------------------------------

    def _deterministic_generate(self, profile: DomainProfile) -> Strategy:
        domain = profile.domain_name.lower()

        if "security" in domain:
            return Strategy(
                checklist=[
                    "sql_injection",
                    "hardcoded_secret",
                    "command_injection",
                    "path_traversal",
                    "insecure_eval",
                    "weak_password_hash",
                    "debug_enabled",
                    "open_redirect",
                    "insecure_deserialization",
                ],
                output_format={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": "vulnerability type label",
                            "severity": "low | medium | high | critical",
                            "file": "source filename",
                            "evidence": "code snippet showing the issue",
                            "fix": "suggested remediation",
                        },
                    },
                },
                analysis_approach=(
                    "For each file, systematically check every item in the "
                    "checklist. Look for dangerous function calls, insecure "
                    "patterns, hardcoded values, and missing input validation. "
                    "Extract the offending line as evidence and suggest a fix."
                ),
                severity_levels=["low", "medium", "high", "critical"],
            )

        # Generic fallback
        return Strategy(
            checklist=["general_issues"],
            output_format={"type": "array"},
            analysis_approach="Analyze code for common issues.",
            severity_levels=["low", "medium", "high"],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        m = re.search(r'\{[\s\S]+\}', raw)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}
