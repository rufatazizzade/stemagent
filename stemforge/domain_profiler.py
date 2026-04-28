"""StemForge — Domain Profiler.

Reads domain tasks and sample files, then produces a structured
DomainProfile describing the domain's characteristics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from stemforge.llm import BaseLLM
from stemforge.models import DomainProfile


class DomainProfiler:
    """Analyzes a domain directory to produce a DomainProfile."""

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def profile(self, domain_dir: Path) -> DomainProfile:
        """Generate a domain profile from the tasks and samples.

        Parameters
        ----------
        domain_dir : Path
            Directory containing ``tasks.json`` and ``samples/``.

        Returns
        -------
        DomainProfile
        """
        tasks_path = domain_dir / "tasks.json"
        with open(tasks_path, "r", encoding="utf-8") as f:
            tasks_data = json.load(f)

        # Gather sample file contents for context
        samples_dir = domain_dir / tasks_data.get("samples_dir", "samples")
        sample_summaries = self._read_samples(samples_dir)

        # Try LLM-based profiling; fall back to deterministic extraction
        try:
            return self._llm_profile(tasks_data, sample_summaries)
        except Exception:
            return self._deterministic_profile(tasks_data)

    # ------------------------------------------------------------------
    # LLM-based profiling
    # ------------------------------------------------------------------

    def _llm_profile(self, tasks_data: dict, sample_summaries: str) -> DomainProfile:
        system = (
            "You are an expert domain analyst. Given a set of tasks and code "
            "samples, produce a JSON domain profile with these keys: "
            "domain_name, task_type, common_approach, required_skills (list), "
            "possible_tools (list), output_schema (dict), evaluation_criteria (list)."
        )
        user = (
            f"Tasks definition:\n{json.dumps(tasks_data, indent=2)}\n\n"
            f"Sample file summaries:\n{sample_summaries}"
        )
        raw = self.llm.call(system, user)
        data = self._parse_json(raw)
        return DomainProfile(**data)

    # ------------------------------------------------------------------
    # Deterministic fallback
    # ------------------------------------------------------------------

    def _deterministic_profile(self, tasks_data: dict) -> DomainProfile:
        domain = tasks_data.get("domain", "unknown")
        task_type = tasks_data.get("task_type", "analysis")

        profiles = {
            "security": DomainProfile(
                domain_name="security code review",
                task_type="code_review",
                common_approach=(
                    "Inspect source code for known vulnerability classes, "
                    "match against established patterns, extract evidence, "
                    "and suggest safe remediations."
                ),
                required_skills=[
                    "code reading",
                    "vulnerability taxonomy",
                    "evidence extraction",
                    "safe fix generation",
                ],
                possible_tools=[
                    "static analysis",
                    "pattern matching",
                    "AST parsing",
                    "taint analysis",
                ],
                output_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": "string",
                            "severity": "string",
                            "file": "string",
                            "evidence": "string",
                            "fix": "string",
                        },
                    },
                },
                evaluation_criteria=[
                    "precision of vulnerability detection",
                    "recall across vulnerability classes",
                    "accuracy of severity ratings",
                    "quality of remediation suggestions",
                ],
            ),
            "qa": DomainProfile(
                domain_name="quality assurance review",
                task_type="test_review",
                common_approach="Analyze code for test coverage and quality.",
                required_skills=["test design", "coverage analysis"],
                possible_tools=["coverage.py", "pytest"],
                output_schema={"type": "array"},
                evaluation_criteria=["coverage accuracy"],
            ),
        }

        return profiles.get(domain, DomainProfile(
            domain_name=domain,
            task_type=task_type,
            common_approach="Analyze tasks and produce findings.",
            required_skills=["analysis"],
            possible_tools=[],
            output_schema={"type": "array"},
            evaluation_criteria=["accuracy"],
        ))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_samples(samples_dir: Path, max_lines: int = 20) -> str:
        """Read the first ``max_lines`` of each sample for context."""
        if not samples_dir.exists():
            return "(no samples found)"
        summaries: List[str] = []
        for p in sorted(samples_dir.glob("*.py")):
            lines = p.read_text(encoding="utf-8").splitlines()[:max_lines]
            summaries.append(f"--- {p.name} ---\n" + "\n".join(lines))
        return "\n\n".join(summaries)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Best-effort JSON extraction from LLM output."""
        import re
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Try extracting a JSON block
        m = re.search(r'\{[\s\S]+\}', raw)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {}
