# StemForge — Write-Up

## 1. Problem Interpretation

The challenge is to build a **universal stem agent** — an AI agent that starts
with no domain expertise and acquires it through a structured self-specialization
process.  The key insight is that universality lives not in the agent's knowledge
but in the **procedure** that transforms it.

A security specialist, a QA reviewer, and a research analyst are all possible
outputs of the same loop.  We chose security code review as the demonstration
domain because it offers clear ground truth and measurable metrics.

---

## 2. Approach

We decomposed the problem into five atomic stages, each with a single
responsibility:

1. **Profile** — understand what kind of tasks the domain contains.
2. **Strategize** — derive a checklist and output schema from the profile.
3. **Build** — assemble a specialist agent configuration.
4. **Evaluate** — measure the specialist against ground truth.
5. **Safeguard** — accept the specialist only if it improves on the baseline.

Each stage is implemented as a standalone module with a clean interface, making
the loop easy to extend and debug.

---

## 3. Architecture

```
StemAgent  ──▶  DomainProfiler  ──▶  StrategyGenerator
                                           │
                                           ▼
Safeguards ◀── Evaluator ◀── SpecialistAgent ◀── AgentBuilder
```

**Data flow:** The loop starts with raw tasks and sample files.  The
DomainProfiler reads them and produces a `DomainProfile` — a structured
description of the domain.  The StrategyGenerator transforms that into a
`Strategy` (checklist, output format, approach).  The AgentBuilder combines
profile and strategy into an `AgentConfig` with a specialized system prompt.
The SpecialistAgent uses that config to analyze code.  The Evaluator scores
it.  The Safeguards module gates acceptance.

**LLM abstraction:** The `BaseLLM` interface allows swapping between OpenAI
and a deterministic MockLLM.  The mock mode enables full testing without API
access and makes results reproducible.

**Models:** All data structures use Pydantic for validation and serialization:
`Finding`, `AgentConfig`, `DomainProfile`, `Strategy`, `EvaluationResult`,
`SafeguardDecision`.

---

## 4. Specialization Loop

The stem agent is universal not because it directly solves every task, but
because the specialization procedure is domain-agnostic: profile the task
family, generate a strategy, build a specialist, evaluate it, and accept or
roll back changes.

### Iteration and Early Stopping

The loop supports multiple iterations.  Each iteration can refine the strategy
by feeding back missed vulnerability types from the previous evaluation.  The
loop stops early if:

- Improvement is less than 0.03 for two consecutive iterations, or
- The maximum number of iterations is reached.

In mock mode, the first iteration typically achieves the maximum score because
the pattern-matching rules are deterministic.  With a real LLM, iterative
refinement would show more gradual improvement.

---

## 5. Evaluation Setup

### Benchmark

Ten Python files, each containing a single vulnerability class (or none):

| File                        | Expected Label            |
|-----------------------------|---------------------------|
| `sql_injection.py`         | sql_injection             |
| `hardcoded_secret.py`      | hardcoded_secret          |
| `command_injection.py`     | command_injection         |
| `path_traversal.py`        | path_traversal            |
| `insecure_eval.py`         | insecure_eval             |
| `weak_password_hash.py`    | weak_password_hash        |
| `debug_enabled.py`         | debug_enabled             |
| `open_redirect.py`         | open_redirect             |
| `insecure_deserialization.py` | insecure_deserialization |
| `safe_code.py`             | *(none)*                  |

### Metrics

- **Precision** = TP / (TP + FP) — are the agent's alerts accurate?
- **Recall** = TP / (TP + FN) — does the agent catch everything?
- **F1** = harmonic mean — balanced measure.

### Baseline vs. Evolved

The baseline stem agent uses a generic prompt ("Analyze the task and produce
useful findings").  It intentionally lacks a security checklist and can only
detect the most obvious patterns.

The evolved specialist receives a detailed system prompt with a full checklist,
severity definitions, and a structured output schema.

---

## 6. Benchmark Results (Deterministic)

To ensure reproducibility, the primary benchmark is reported using the **MockLLM** backend. This eliminates the inherent variance of commercial LLM APIs and focuses on the mechanical effectiveness of the specialization loop.

| Version              | Precision | Recall | F1     |
|----------------------|-----------|--------|--------|
| Baseline stem agent  | 1.0000    | 0.3333 | 0.5000 |
| Evolved specialist   | 1.0000    | 1.0000 | 1.0000 |

**Total F1 Improvement: +0.5000**

The baseline universal agent detects only the three most obvious vulnerability patterns (hardcoded secrets, debug mode, and insecure eval). After the specialization loop, the evolved specialist receives a comprehensive security checklist that enables it to detect all 9 vulnerability classes with perfect precision.

### 6.1 Additional Validation (GPT-4o-mini)

When using a real LLM (OpenAI `gpt-4o-mini`), the system demonstrates even more significant qualitative gains. While the baseline agent with a generic prompt often produces vague or redundant findings, the specialized agent follows the generated strategy with high rigor.

### Iteration Dynamics (Real LLM)

| Iteration | Strategy Change                            | F1     |
|-----------|--------------------------------------------|--------|
| Baseline  | Generic prompt, no checklist               | 0.5455 |
| 1         | Generated 9-item checklist                 | 1.0000 |
| 2         | Same checklist (converged)                 | 1.0000 |
| 3         | Same checklist → early stop triggered      | 1.0000 |

The safeguard gate accepted the evolved agent in every run.

---

## 7. What Surprised Us

- **How much the system prompt matters.**  The same underlying LLM produces
  dramatically different results when given a checklist vs. a generic
  instruction.  GPT-4o-mini went from 0.55 F1 to 1.0 F1 with *only* a
  prompt change — no fine-tuning, no extra data.

- **Label normalization is a hidden bottleneck.**  The real LLM returns
  creative label variants (`debug_mode_enabled_in_production`,
  `weak_password_hashing_sha1`, `insecure_deserialization_via_cookie`).
  Without an alias table and suffix stripping, the evaluator would
  undercount true positives and inflate false positives, making the
  specialization loop's gains appear smaller than they actually are.

- **The mock is more educational than expected.**  Building deterministic
  baseline and evolved rule sets forced us to think carefully about what
  "specialization" actually means at a mechanical level.

- **The evaluation-driven loop is self-correcting.**  The safeguard gate
  prevents regressions, and the iteration feedback loop provides a natural
  channel for refinement.

---

## 8. What Failed

- **Label normalization required iteration.**  Our first real-LLM run
  showed 0.17 baseline F1 and 0.74 evolved F1 — misleadingly low because
  the evaluator treated `path_traversal_vulnerability` and `path_traversal`
  as different labels.  We had to add an alias table with 60+ mappings.

- **LLM-based profiling is fragile.**  The domain profiler sometimes returns
  malformed JSON or hallucinated fields.  We added deterministic fallbacks
  for robustness, but a production system would need structured extraction
  (e.g., function calling / structured outputs).

- **The strategy generator needs grounding.**  Without explicit snake_case
  label examples in the prompt, the LLM produces human-readable checklist
  items like "SQL Injection" that don't match evaluation labels.

- **The QA domain is a stub.**  We only implemented the security benchmark.
  Demonstrating true universality would require at least two fully worked
  domains.

---

## 9. What We Would Do with More Time

1. **Multiple fully-worked domains** — QA, accessibility review, performance
   analysis — to prove the loop is truly domain-agnostic.

2. **LLM function calling** — Use structured output / tool-use APIs instead
   of raw JSON extraction for more reliable profiling and strategy generation.

3. **Richer benchmarks** — Files with multiple vulnerabilities, subtle bugs,
   and adversarial safe code to stress-test precision.

4. **Strategy refinement with feedback** — Pass the per-file confusion matrix
   back to the StrategyGenerator to evolve the checklist over iterations.

5. **Agent memory** — Let the specialist accumulate knowledge across files
   (e.g., taint tracking across imports).

6. **Human-in-the-loop** — Add a review step where a human can approve or
   modify the generated strategy before building the specialist.

7. **Multi-agent composition** — Compose specialists from different domains
   into a pipeline (e.g., security → QA → performance).

---

*StemForge is a research prototype demonstrating evaluation-driven agent
specialization.  The core contribution is the loop, not any individual
component.*
