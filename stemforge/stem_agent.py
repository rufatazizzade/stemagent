"""StemForge — Universal Stem Agent.

The baseline agent uses a deliberately generic prompt with no
domain-specific knowledge.  It demonstrates what a minimal
universal agent can achieve before specialization.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

from stemforge.llm import BaseLLM
from stemforge.models import AgentConfig, Finding


class StemAgent:
    """Minimal universal agent — no domain-specific instructions."""

    DEFAULT_SYSTEM_PROMPT = (
        "Analyze this task and return only the most obvious issues. "
        "Do not use any domain-specific checklist. "
        "Return your response as a JSON object with a 'findings' array. "
        "Each finding must have these keys: type, severity, file, evidence, fix. "
        "If no issues are found, return {\"findings\": []}."
    )

    def __init__(self, llm: BaseLLM, config: AgentConfig | None = None):
        self.llm = llm
        self.config = config or AgentConfig(
            role="universal analysis agent",
            domain="general",
            system_prompt=self.DEFAULT_SYSTEM_PROMPT,
        )

    def analyze_file(self, filepath: Path) -> List[Finding]:
        """Analyze a single file and return findings.

        Parameters
        ----------
        filepath : Path
            Path to the source file to analyze.

        Returns
        -------
        list[Finding]
        """
        code = filepath.read_text(encoding="utf-8")
        user_prompt = (
            f"Analyze this code for any issues.\n"
            f"file: {filepath.name}\n\n"
            f"{code}"
        )
        raw = self.llm.call(self.config.system_prompt, user_prompt)
        return self._parse_findings(raw, filepath.name)

    def analyze_directory(self, directory: Path, max_files: int | None = None) -> Dict[str, List[Finding]]:
        """Analyze Python files in a directory.

        Returns
        -------
        dict
            Mapping of ``filename -> list[Finding]``.
        """
        results: Dict[str, List[Finding]] = {}
        files = sorted(directory.glob("*.py"))
        if max_files:
            files = files[:max_files]
        for path in files:
            results[path.name] = self.analyze_file(path)
        return results

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_findings(raw: str, filename: str) -> List[Finding]:
        """Parse LLM output into Finding objects."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from mixed output
            m = re.search(r'\{[\s\S]*\}', raw)
            if m:
                try:
                    data = json.loads(m.group())
                except json.JSONDecodeError:
                    return []
            else:
                return []

        findings_raw = data.get("findings", [])
        findings: List[Finding] = []
        for item in findings_raw:
            if isinstance(item, dict):
                item.setdefault("file", filename)
                try:
                    findings.append(Finding(**item))
                except Exception:
                    continue
        return findings
