"""StemForge — Agent Builder.

Combines a DomainProfile and Strategy into an AgentConfig and
persists it as a JSON file under ``agents/``.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from stemforge.models import AgentConfig, DomainProfile, Strategy


class AgentBuilder:
    """Builds and saves specialist agent configurations."""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        profile: DomainProfile,
        strategy: Strategy,
        version: str = "1.0",
    ) -> AgentConfig:
        """Create an AgentConfig from a profile and strategy.

        Parameters
        ----------
        profile : DomainProfile
        strategy : Strategy
        version : str
            Version label for this agent config.

        Returns
        -------
        AgentConfig
        """
        checklist_text = "\n".join(f"  - {item}" for item in strategy.checklist)

        # Build a mapping of checklist items to their snake_case labels
        canonical_labels = [
            item.strip().lower().replace(" ", "_").replace("-", "_")
            for item in strategy.checklist
        ]
        labels_text = ", ".join(canonical_labels)

        system_prompt = (
            f"You are a security review specialist agent.\n"
            f"Domain: {profile.domain_name}\n"
            f"Task type: {profile.task_type}\n\n"
            f"CHECKLIST - check every file for:\n{checklist_text}\n\n"
            f"Analysis approach:\n{strategy.analysis_approach}\n\n"
            f"CRITICAL OUTPUT RULES:\n"
            f"1. Return a JSON object with a 'findings' array.\n"
            f"2. Each finding MUST have these keys: type, severity, file, evidence, fix.\n"
            f"3. The 'type' field MUST use one of these exact snake_case labels: "
            f"{labels_text}\n"
            f"4. The 'severity' field must be one of: low, medium, high, critical.\n"
            f"5. The 'file' field must be the source filename.\n"
            f"6. The 'evidence' field must contain the offending code line.\n"
            f"7. The 'fix' field must suggest a remediation.\n"
            f"8. If no issues are found, return {{\"findings\": []}}.\n"
            f"9. Do NOT use vague labels like 'security_vulnerability' or 'code_quality'.\n"
            f"10. Do NOT add suffixes like '_vulnerability' or '_issue' to type labels.\n"
        )

        config = AgentConfig(
            role=f"{profile.domain_name} specialist agent",
            domain=profile.domain_name,
            checklist=strategy.checklist,
            output_schema=strategy.output_format,
            evaluation_target=profile.task_type,
            version=version,
            system_prompt=system_prompt,
            created_at=datetime.now().isoformat(),
        )

        return config

    def save(self, config: AgentConfig, name: str) -> Path:
        """Save agent config to a JSON file.

        Returns the path of the saved file.
        """
        path = self.agents_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2)
        return path
