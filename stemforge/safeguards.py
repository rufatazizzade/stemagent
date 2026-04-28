"""StemForge — Safeguards module.

Compares baseline and evolved evaluation results and decides
whether to accept or reject the evolved specialist agent.
"""

from __future__ import annotations

import json
from pathlib import Path

from stemforge.models import EvaluationResult, SafeguardDecision


class Safeguards:
    """Gate that prevents regressions in agent quality."""

    @staticmethod
    def decide(
        baseline: EvaluationResult,
        evolved: EvaluationResult,
    ) -> SafeguardDecision:
        """Accept the evolved agent only if F1 did not regress.

        Returns
        -------
        SafeguardDecision
        """
        improvement = round(evolved.f1 - baseline.f1, 4)

        if evolved.f1 >= baseline.f1:
            return SafeguardDecision(
                accepted=True,
                reason=(
                    f"Accepted evolved agent because F1 improved from "
                    f"{baseline.f1:.4f} to {evolved.f1:.4f} (+{improvement:.4f})."
                ),
                baseline_f1=baseline.f1,
                evolved_f1=evolved.f1,
                improvement=improvement,
            )
        else:
            return SafeguardDecision(
                accepted=False,
                reason=(
                    f"Rejected evolved agent because F1 regressed from "
                    f"{baseline.f1:.4f} to {evolved.f1:.4f} ({improvement:.4f})."
                ),
                baseline_f1=baseline.f1,
                evolved_f1=evolved.f1,
                improvement=improvement,
            )

    @staticmethod
    def save_summary(decision: SafeguardDecision, path: Path) -> None:
        """Persist the safeguard decision to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(decision.model_dump(), f, indent=2)
