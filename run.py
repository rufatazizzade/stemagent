#!/usr/bin/env python3
"""StemForge — Main entry point.

Runs the full specialization loop:
  1. Baseline evaluation
  2. Domain profiling
  3. Strategy generation
  4. Agent building
  5. Evolved evaluation
  6. Safeguard decision
  7. Iteration with early-stop

Usage:
    python run.py --domain security --iterations 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any other imports that read env vars
try:
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except Exception:
    pass  # Continue without .env — MockLLM will be used

from stemforge.llm import get_llm
from stemforge.stem_agent import StemAgent
from stemforge.domain_profiler import DomainProfiler
from stemforge.strategy_generator import StrategyGenerator
from stemforge.agent_builder import AgentBuilder
from stemforge.specialist_agent import SpecialistAgent
from stemforge.evaluator import Evaluator
from stemforge.safeguards import Safeguards
from stemforge.models import EvaluationResult


# ------------------------------------------------------------------
# Pretty-printing helpers
# ------------------------------------------------------------------

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")


def step(num: int, text: str) -> None:
    print(f"\n{BOLD}{YELLOW}[{num}]{RESET} {BOLD}{text}{RESET}")
    print(f"{DIM}{'-' * 56}{RESET}")


def metric(label: str, value: float) -> None:
    color = GREEN if value >= 0.7 else YELLOW if value >= 0.4 else RED
    print(f"  {label:.<30s} {color}{value:.4f}{RESET}")


def print_table(baseline: EvaluationResult, evolved: EvaluationResult) -> None:
    print(f"\n{BOLD}{'Version':<30s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s}{RESET}")
    print(f"{'-' * 62}")
    print(
        f"{'Baseline universal stem':<30s} "
        f"{baseline.precision:>10.4f} {baseline.recall:>10.4f} {baseline.f1:>10.4f}"
    )
    print(
        f"{GREEN}{'Evolved specialist':<30s} "
        f"{evolved.precision:>10.4f} {evolved.recall:>10.4f} {evolved.f1:>10.4f}{RESET}"
    )
    print(f"{'-' * 62}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="StemForge — Universal Stem Agent Specialization System",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="security",
        help="Domain to specialize for (default: security)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Maximum specialization iterations (default: 3)",
    )
    args = parser.parse_args()

    # Resolve paths
    project_root = Path(__file__).resolve().parent
    domain_dir = project_root / "domains" / args.domain
    agents_dir = project_root / "agents"
    expected_path = domain_dir / "expected.json"
    samples_dir = domain_dir / "samples"

    if not domain_dir.exists():
        print(f"{RED}Error: Domain directory not found: {domain_dir}{RESET}")
        sys.exit(1)

    # Initialize components
    llm = get_llm()

    header("StemForge: Universal Stem Agent Specialization")
    print(f"  LLM backend : {llm.name()}")
    print(f"  Domain      : {args.domain}")
    print(f"  Iterations  : {args.iterations}")

    # ── Step 1: Baseline ──────────────────────────────────────────
    step(1, "Running baseline universal stem agent...")

    stem = StemAgent(llm)
    evaluator = Evaluator(expected_path)
    baseline_result = evaluator.analyze_and_evaluate(stem, samples_dir)

    metric("Baseline Precision", baseline_result.precision)
    metric("Baseline Recall", baseline_result.recall)
    metric("Baseline F1", baseline_result.f1)

    # ── Step 2: Domain profiling ──────────────────────────────────
    step(2, "Profiling domain...")

    profiler = DomainProfiler(llm)
    profile = profiler.profile(domain_dir)

    print(f"  Detected domain  : {profile.domain_name}")
    print(f"  Typical approach : {profile.common_approach[:80]}...")
    print(f"  Required skills  : {', '.join(profile.required_skills)}")

    # ── Iteration loop ────────────────────────────────────────────
    strat_gen = StrategyGenerator(llm)
    builder = AgentBuilder(agents_dir)
    best_result = baseline_result
    best_config = None
    consecutive_small = 0
    prev_f1 = baseline_result.f1
    final_evolved_result = baseline_result  # default if no iteration accepted

    for iteration in range(1, args.iterations + 1):
        # ── Step 3: Strategy generation ───────────────────────────
        step(3, f"Generating specialist strategy (iteration {iteration}/{args.iterations})...")

        strategy = strat_gen.generate(
            profile,
            previous_result=best_result if iteration > 1 else None,
            iteration=iteration,
        )

        print("  Checklist:")
        for item in strategy.checklist:
            print(f"    - {item}")

        # ── Step 4: Build evolved agent ───────────────────────────
        step(4, f"Building evolved specialist agent v{iteration}.0...")

        config = builder.build(profile, strategy, version=f"{iteration}.0")
        config_path = builder.save(config, f"evolved_{args.domain}_agent")
        print(f"  Saved: {config_path}")

        # ── Step 5: Evaluate evolved agent ────────────────────────
        step(5, "Evaluating evolved agent...")

        specialist = SpecialistAgent(llm, config)
        evolved_result = evaluator.analyze_and_evaluate(specialist, samples_dir)

        metric("Evolved Precision", evolved_result.precision)
        metric("Evolved Recall", evolved_result.recall)
        metric("Evolved F1", evolved_result.f1)

        # ── Step 6: Safeguard decision ────────────────────────────
        step(6, "Safeguard decision:")

        decision = Safeguards.decide(baseline_result, evolved_result)
        color = GREEN if decision.accepted else RED
        print(f"  {color}{decision.reason}{RESET}")

        Safeguards.save_summary(
            decision,
            project_root / "agents" / f"safeguard_decision_iter{iteration}.json",
        )

        if decision.accepted and evolved_result.f1 > best_result.f1:
            best_result = evolved_result
            best_config = config
            final_evolved_result = evolved_result

        # ── Stop condition ────────────────────────────────────────
        improvement = evolved_result.f1 - prev_f1
        prev_f1 = evolved_result.f1

        if abs(improvement) < 0.03:
            consecutive_small += 1
        else:
            consecutive_small = 0

        if consecutive_small >= 2:
            print(f"\n  {YELLOW}Stopping early: improvement < 0.03 for 2 consecutive iterations.{RESET}")
            break

    # ── Final summary ─────────────────────────────────────────────
    header("Final Before / After Comparison")
    print_table(baseline_result, final_evolved_result)

    improvement = final_evolved_result.f1 - baseline_result.f1
    if improvement > 0:
        print(f"\n  {GREEN}[+] Specialization improved F1 by {improvement:.4f}{RESET}")
    elif improvement == 0:
        print(f"\n  {YELLOW}[=] No change in F1{RESET}")
    else:
        print(f"\n  {RED}[-] Specialization did not improve F1{RESET}")

    # Save final results
    results_path = project_root / "agents" / "final_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "baseline": baseline_result.model_dump(),
                "evolved": final_evolved_result.model_dump(),
                "improvement": improvement,
            },
            f,
            indent=2,
        )
    print(f"\n  Results saved to: {results_path}")


if __name__ == "__main__":
    main()
