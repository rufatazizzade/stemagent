"""StemForge — Evaluator module.

Compares agent findings against expected labels to compute
precision, recall, and F1 score.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set

from stemforge.models import EvaluationResult, Finding


class Evaluator:
    """Compares agent output to ground-truth expected labels."""

    def __init__(self, expected_path: Path):
        with open(expected_path, "r", encoding="utf-8") as f:
            self.expected: Dict[str, List[str]] = json.load(f)

    def evaluate(self, all_findings: Dict[str, List[Finding]]) -> EvaluationResult:
        """Compute precision / recall / F1 over the full benchmark.

        Parameters
        ----------
        all_findings : dict
            Mapping of ``filename -> list[Finding]`` produced by the agent.

        Returns
        -------
        EvaluationResult
        """
        tp = 0
        fp = 0
        fn = 0
        per_file: Dict[str, dict] = {}

        for filename, expected_labels in self.expected.items():
            expected_set: Set[str] = {self._normalize(l) for l in expected_labels}
            detected_set: Set[str] = set()

            for finding in all_findings.get(filename, []):
                normalized = self._normalize(finding.type)
                # Skip labels too vague to match anything specific
                if normalized not in self.IGNORE_LABELS:
                    detected_set.add(normalized)

            file_tp = len(expected_set & detected_set)
            file_fp = len(detected_set - expected_set)
            file_fn = len(expected_set - detected_set)

            tp += file_tp
            fp += file_fp
            fn += file_fn

            per_file[filename] = {
                "expected": sorted(expected_set),
                "detected": sorted(detected_set),
                "tp": file_tp,
                "fp": file_fp,
                "fn": file_fn,
            }

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return EvaluationResult(
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            details=per_file,
        )

    # Common aliases the LLM may use instead of the canonical labels
    LABEL_ALIASES: Dict[str, str] = {
        # sql_injection variants
        "sql_injection_vulnerability": "sql_injection",
        "sqli": "sql_injection",
        "sql_injection_via_string_formatting": "sql_injection",
        "sql_injection_via_concatenation": "sql_injection",
        # hardcoded_secret variants
        "hardcoded_credentials": "hardcoded_secret",
        "hardcoded_secrets": "hardcoded_secret",
        "hardcoded_password": "hardcoded_secret",
        "hardcoded_api_key": "hardcoded_secret",
        "hardcoded_token": "hardcoded_secret",
        "sensitive_data_exposure": "hardcoded_secret",
        "exposed_secret": "hardcoded_secret",
        # command_injection variants
        "command_injection_vulnerability": "command_injection",
        "os_command_injection": "command_injection",
        "cmd_injection": "command_injection",
        "shell_injection": "command_injection",
        # path_traversal variants
        "path_traversal_vulnerability": "path_traversal",
        "directory_traversal": "path_traversal",
        "file_read_vulnerability": "path_traversal",
        "direct_file_access": "path_traversal",
        "direct_file_read": "path_traversal",
        "arbitrary_file_read": "path_traversal",
        "file_inclusion": "path_traversal",
        # insecure_eval variants
        "insecure_eval_vulnerability": "insecure_eval",
        "insecure_eval_usage": "insecure_eval",
        "insecure_exec_usage": "insecure_eval",
        "code_injection": "insecure_eval",
        "eval_injection": "insecure_eval",
        "arbitrary_code_execution": "insecure_eval",
        # weak_password_hash variants
        "weak_hashing": "weak_password_hash",
        "weak_hash": "weak_password_hash",
        "insecure_hashing": "weak_password_hash",
        "weak_cryptography": "weak_password_hash",
        "weak_password_hashing": "weak_password_hash",
        "weak_password_hashing_md5": "weak_password_hash",
        "weak_password_hashing_sha1": "weak_password_hash",
        "insecure_password_hashing": "weak_password_hash",
        "md5_password_hashing": "weak_password_hash",
        "sha1_password_hashing": "weak_password_hash",
        # debug_enabled variants
        "debug_mode": "debug_enabled",
        "debug_mode_enabled": "debug_enabled",
        "debug_enabled_vulnerability": "debug_enabled",
        "debug_mode_enabled_in_production": "debug_enabled",
        "debug_mode_on": "debug_enabled",
        "flask_debug_mode": "debug_enabled",
        # open_redirect variants
        "open_redirect_vulnerability": "open_redirect",
        "unvalidated_redirect": "open_redirect",
        "url_redirect": "open_redirect",
        "unvalidated_redirect_url": "open_redirect",
        # insecure_deserialization variants
        "insecure_deserialization_vulnerability": "insecure_deserialization",
        "unsafe_deserialization": "insecure_deserialization",
        "pickle_deserialization": "insecure_deserialization",
        "insecure_deserialization_via_cookie": "insecure_deserialization",
        "insecure_pickle_deserialization": "insecure_deserialization",
    }

    # Suffixes that can be stripped during normalization
    STRIP_SUFFIXES = [
        "_vulnerability", "_issue", "_risk", "_flaw", "_bug", "_problem",
    ]

    # Labels too vague to count as a specific finding
    IGNORE_LABELS = {
        "security_vulnerability", "security_issue", "code_quality",
        "security_best_practices", "best_practice", "general_issue",
        "code_smell",
    }

    @classmethod
    def _normalize(cls, label: str) -> str:
        """Normalize a vulnerability label for comparison.

        Handles common LLM label variants by:
        1. Lowercasing and replacing separators with underscores
        2. Stripping generic suffixes (_vulnerability, _issue, etc.)
        3. Mapping known aliases to canonical labels
        """
        s = label.strip().lower().replace("-", "_").replace(" ", "_")

        # Check alias table first (before stripping)
        if s in cls.LABEL_ALIASES:
            return cls.LABEL_ALIASES[s]

        # Strip generic suffixes
        for suffix in cls.STRIP_SUFFIXES:
            if s.endswith(suffix) and len(s) > len(suffix):
                s = s[: -len(suffix)]
                break

        # Check alias table again after stripping
        if s in cls.LABEL_ALIASES:
            return cls.LABEL_ALIASES[s]

        return s
