# StemForge — Universal Stem Agent Specialization System

> A domain-agnostic framework that transforms a minimal universal agent into a
> measurably superior specialist through an evaluation-driven self-specialization loop.

---

## Why "Stem Agent"?

Like a biological stem cell, the **stem agent** starts as a generic, undifferentiated
entity.  It doesn't know security, QA, or any specific domain.  Through a repeatable
specialization procedure — profile, strategize, build, evaluate, accept-or-rollback —
it differentiates into a domain expert.

**The agent is universal not because it directly solves every task**, but because the
specialization procedure itself is domain-agnostic.

## Why Security as the Demo Domain?

Security code review was chosen because it allows **measurable evaluation**: we have
concrete vulnerability labels, a clear ground truth, and well-defined metrics
(precision, recall, F1).  The same loop can theoretically specialize the agent into
a QA reviewer, a research analyst, or any other domain.

---

## Architecture

```
┌──────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│  Stem Agent  │─────▶│  Domain Profiler  │─────▶│ Strategy Generator  │
│  (baseline)  │      │  (analyze tasks)  │      │ (build checklist)   │
└──────────────┘      └──────────────────┘      └─────────┬───────────┘
                                                          │
                                                          ▼
┌──────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│  Safeguards  │◀─────│    Evaluator     │◀─────│   Agent Builder     │
│ (accept/rej) │      │ (P / R / F1)     │      │ (specialist config) │
└──────────────┘      └──────────────────┘      └─────────────────────┘
```

### Specialization Loop

1. **Baseline** — Run the generic stem agent; measure F1.
2. **Profile** — Analyze domain tasks and samples.
3. **Strategize** — Generate a vulnerability checklist and output schema.
4. **Build** — Create a specialist agent config with a detailed system prompt.
5. **Evaluate** — Run the specialist; compute precision / recall / F1.
6. **Safeguard** — Accept only if F1 ≥ baseline; otherwise rollback.
7. **Iterate** — Repeat with feedback; stop when improvement < 0.03 for 2 rounds.

---

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) An OpenAI API key

### Setup

```bash
# Clone or enter the project directory
cd stemforge

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# (Optional) Set your OpenAI key
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Running — For Reproducible Evaluation (Mock LLM)

```bash
# Recommended for consistent, deterministic benchmark results
python run.py --domain security --iterations 3 --mock
```

The MockLLM uses deterministic pattern matching to simulate the specialization
improvement, producing identical results on every run.

### Running — With Real LLM (OpenAI)

```bash
# Set your OPENAI_API_KEY in .env first
python run.py --domain security --iterations 3
```

---

## Evaluation

Evaluate individual agents against a domain benchmark:

```bash
# Baseline agent
python evaluate.py --agent baseline --domain security

# Evolved specialist (must run `run.py` first)
python evaluate.py --agent evolved --domain security
```

### Metrics

| Metric    | Definition                          |
|-----------|-------------------------------------|
| Precision | TP / (TP + FP) — accuracy of alerts |
| Recall    | TP / (TP + FN) — coverage           |
| F1        | Harmonic mean of P and R            |

---

## Example Output (Mock LLM)

```
══════════════════════════════════════════════════════════════
  StemForge: Universal Stem Agent Specialization
══════════════════════════════════════════════════════════════

  LLM backend : MockLLM (deterministic)
  Domain      : security
  Iterations  : 3

[1] Running baseline universal stem agent...
  Baseline Precision............. 1.0000
  Baseline Recall................ 0.3333
  Baseline F1.................... 0.5000

[2] Profiling domain...
  Detected domain  : security code review
  Required skills  : code reading, vulnerability taxonomy, ...

[3] Generating specialist strategy (iteration 1/3)...
  Checklist:
    - sql_injection
    - hardcoded_secret
    - command_injection
    ...

[4] Building evolved specialist agent v1.0...
  Saved: agents\evolved_security_agent.json

[5] Evaluating evolved agent...
  Evolved Precision.............. 1.0000
  Evolved Recall................. 1.0000
  Evolved F1..................... 1.0000

[6] Safeguard decision:
  Accepted evolved agent because F1 improved from 0.5000 to 1.0000

══════════════════════════════════════════════════════════════
  Final Before / After Comparison
══════════════════════════════════════════════════════════════

Version                        Precision    Recall        F1
──────────────────────────────────────────────────────────────
Baseline universal stem             1.0000    0.3333    0.5000
Evolved specialist                  1.0000    1.0000    1.0000
──────────────────────────────────────────────────────────────

  ✓ Specialization improved F1 by 0.5000
```

---

## Project Structure

```
stemforge/
├── README.md               # This file
├── WRITEUP.md              # Detailed write-up
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment config
├── .gitignore
├── run.py                  # Main specialization loop
├── evaluate.py             # Standalone evaluator
│
├── stemforge/              # Core library
│   ├── __init__.py
│   ├── models.py           # Pydantic data models
│   ├── llm.py              # LLM abstraction (OpenAI + Mock)
│   ├── stem_agent.py       # Baseline universal agent
│   ├── domain_profiler.py  # Domain analysis
│   ├── strategy_generator.py  # Specialist strategy creation
│   ├── agent_builder.py    # Agent config assembly
│   ├── specialist_agent.py # Evolved specialist agent
│   ├── evaluator.py        # Precision / Recall / F1
│   └── safeguards.py       # Accept / reject gate
│
├── domains/                # Domain benchmarks
│   ├── security/
│   │   ├── tasks.json
│   │   ├── expected.json
│   │   └── samples/        # 10 sample files
│   └── qa/                 # Stub for future domains
│
└── agents/                 # Generated agent configs
    ├── baseline_agent.json
    └── evolved_security_agent.json  (generated)
```

---

## License

Research prototype — not intended for production use.
