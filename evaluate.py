#!/usr/bin/env python3
"""StemForge - Standalone evaluator.

Evaluate either the baseline or evolved agent against a domain benchmark.

Usage:
    python evaluate.py --agent baseline --domain security
    python evaluate.py --agent evolved  --domain security
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except Exception:
    pass

from stemforge.llm import get_llm
from stemforge.stem_agent import StemAgent
from stemforge.specialist_agent import SpecialistAgent
from stemforge.evaluator import Evaluator
from stemforge.models import AgentConfig


CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def main() -> None:
    parser = argparse.ArgumentParser(description="StemForge - Agent Evaluator")
    parser.add_argument(
        "--agent",
        type=str,
        choices=["baseline", "evolved"],
        required=True,
        help="Which agent to evaluate",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="security",
        help="Domain benchmark (default: security)",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    domain_dir = project_root / "domains" / args.domain
    expected_path = domain_dir / "expected.json"
    samples_dir = domain_dir / "samples"

    if not domain_dir.exists():
        print(f"{RED}Error: Domain directory not found: {domain_dir}{RESET}")
        sys.exit(1)

    llm = get_llm()

    print(f"\n{BOLD}{CYAN}StemForge Evaluator{RESET}")
    print(f"  Agent   : {args.agent}")
    print(f"  Domain  : {args.domain}")
    print(f"  LLM     : {llm.name()}\n")

    # Run the appropriate agent
    if args.agent == "baseline":
        agent = StemAgent(llm)
        findings = agent.analyze_directory(samples_dir)
    else:
        config_path = project_root / "agents" / f"evolved_{args.domain}_agent.json"
        if not config_path.exists():
            print(f"{RED}Error: Evolved agent config not found: {config_path}")
            print(f"Run 'python run.py --domain {args.domain}' first.{RESET}")
            sys.exit(1)
        agent = SpecialistAgent.from_file(llm, config_path)
        findings = agent.analyze_directory(samples_dir)

    # Evaluate
    evaluator = Evaluator(expected_path)
    result = evaluator.evaluate(findings)

    # Print results
    print(f"{BOLD}{'Metric':<20s} {'Value':>10s}{RESET}")
    print(f"{'-' * 32}")
    print(f"{'True Positives':<20s} {result.true_positives:>10d}")
    print(f"{'False Positives':<20s} {result.false_positives:>10d}")
    print(f"{'False Negatives':<20s} {result.false_negatives:>10d}")
    print(f"{'-' * 32}")

    def colored(val: float) -> str:
        c = GREEN if val >= 0.7 else YELLOW if val >= 0.4 else RED
        return f"{c}{val:.4f}{RESET}"

    print(f"{'Precision':<20s} {colored(result.precision):>20s}")
    print(f"{'Recall':<20s} {colored(result.recall):>20s}")
    print(f"{'F1':<20s} {colored(result.f1):>20s}")

    # Per-file details
    print(f"\n{BOLD}Per-file breakdown:{RESET}")
    print(f"{'File':<30s} {'Expected':>12s} {'Detected':>12s} {'TP':>4s} {'FP':>4s} {'FN':>4s}")
    print(f"{'-' * 68}")
    for fname, detail in sorted(result.details.items()):
        exp = ",".join(detail["expected"]) or "-"
        det = ",".join(detail["detected"]) or "-"
        print(
            f"{fname:<30s} {exp:>12s} {det:>12s} "
            f"{detail['tp']:>4d} {detail['fp']:>4d} {detail['fn']:>4d}"
        )


if __name__ == "__main__":
    main()
