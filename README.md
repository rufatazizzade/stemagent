# StemForge: Universal Stem Agent Specialization

StemForge is a research prototype that demonstrates a structured process for transforming a generic AI agent into a domain specialist. Like a biological stem cell that can differentiate into various cell types, the "stem agent" in this system begins as a minimal, domain-agnostic entity and evolves through a repeatable specialization loop.

The project addresses the challenge of building specialized agents by focusing not on hardcoded knowledge, but on the *procedure* of specialization. This allows the same core system to adapt to diverse task families—such as security auditing, quality assurance, or deep research—by following a structured, evaluation-driven evolution cycle.

It is important to clarify that the stem agent is universal not because it can directly solve every possible task, but because the specialization process itself is domain-agnostic. The system observes task examples, infers a strategy, builds a specialized configuration, and validates the resulting agent against measurable ground truth.

## Core Idea

The fundamental concept of StemForge is the "Universal to Specialist" transition. Instead of building a security agent or a QA agent from scratch, we build a **specialization loop** that can take a minimal "universal" agent and differentiate it for a specific task family.

In this context, "universal" refers to the domain-agnostic nature of the specialization machinery. The loop is the same regardless of whether the target is cybersecurity or accessibility testing. The agent "specializes" by acquiring a tailored checklist, analysis approach, and output schema through observation and evaluation.

## Architecture

```text
Universal Stem Agent
        |
        v
Domain Profiler
        |
        v
Strategy Generator
        |
        v
Agent Builder
        |
        v
Evaluator
        |
        v
Safeguard / Rollback
        |
        v
Specialist Agent
```

### Modules

- **Domain Profiler**: Analyzes sample tasks and code to understand the domain's characteristics, required skills, and typical patterns.
- **Strategy Generator**: Derives a formal analysis strategy, including a specific checklist of items to look for and a structured output schema.
- **Agent Builder**: Assembles a specialized agent configuration by combining the domain profile and the generated strategy into a detailed system prompt.
- **Specialist Agent**: An evolved agent instance that operates using the specialized configuration to perform high-precision analysis.
- **Evaluator**: Measures the agent's performance (Precision, Recall, F1) against labeled ground truth data.
- **Safeguards**: A gating mechanism that accepts the new specialist only if it demonstrates measurable improvement over the current best version; otherwise, it rolls back changes.
- **LLM Backend**: A unified abstraction layer supporting both deterministic mock mode and real-world OpenAI models.

## Demo Domain: Security Code Review

Security code review was chosen as the demonstration domain because it provides a clear, measurable benchmark. We use a suite of small Python files, each labeled with specific vulnerability classes (or marked as safe). This allows for unambiguous calculation of precision and recall.

The benchmark targets the following vulnerability types:
- `sql_injection`
- `hardcoded_secret`
- `command_injection`
- `path_traversal`
- `insecure_eval`
- `weak_password_hash`
- `debug_enabled`
- `open_redirect`
- `insecure_deserialization`
- `safe_code` (contains no vulnerabilities)

## Setup

1. **Clone the repository and enter the directory.**
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   ```
   - **Windows:** `venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Environment

To use real-world models, create a `.env` file in the root directory:
```text
OPENAI_API_KEY=your_api_key_here
```
**Note:** No API key is required to run the main benchmark in mock mode. The system will use deterministic pattern matching to simulate the specialization process, ensuring reproducible results for evaluation purposes.

## Running the Main Benchmark

To run the full specialization loop using the deterministic MockLLM:
```bash
python run.py --domain security --iterations 3 --mock
```
This command initializes the universal stem agent, profiles the security domain, and runs up to 3 iterations of strategy generation and evaluation. It uses the `--mock` flag to ensure consistent, repeatable results.

## Running with OpenAI

If you have an OpenAI API key configured, you can run the loop with real models:
```bash
python run.py --domain security --iterations 3
```
- The system defaults to `gpt-4o-mini`.
- Calls include a **30-second timeout** and a **max_retries of 1**.
- If an OpenAI call fails or times out, the system gracefully falls back to the **MockLLM** to prevent the loop from crashing.

## Evaluating Agents

You can evaluate individual agents (baseline vs. evolved) against the benchmark:
```bash
# Evaluate the baseline universal agent
python evaluate.py --agent baseline --domain security --mock

# Evaluate the evolved specialist (requires run.py to have been executed first)
python evaluate.py --agent evolved --domain security --mock
```

## Quick Testing

For a fast smoke test of the system logic, use the `--max-files` option to limit the scope:
```bash
python run.py --domain security --iterations 1 --mock --max-files 3
```

## Example Output

A successful run demonstrates the measurable gain from a generic baseline to a specialized agent:

| Version | Precision | Recall | F1 |
| :--- | :--- | :--- | :--- |
| **Baseline universal stem** | 1.0000 | 0.3333 | 0.5000 |
| **Evolved specialist** | 1.0000 | 1.0000 | 1.0000 |

## Output Files

- `agents/evolved_security_agent.json`: The generated configuration (system prompt and strategy) for the specialist.
- `agents/final_results.json`: Detailed metrics and per-file breakdown of the final evaluation.

## Reproducibility Note

The reported benchmark results are based on the deterministic **MockLLM** mode. This ensures that the effectiveness of the specialization loop's *logic* is verified independently of LLM non-determinism or API latency.

## Limitations

- **Small Benchmark**: The demo uses a controlled suite of 10 sample files with clear-cut vulnerabilities.
- **Toy Examples**: Vulnerabilities are represented as simple patterns for demonstration purposes.
- **Configuration-based**: The agent "evolves" by generating a new system prompt and strategy, not by autonomously rewriting its own source code.
- **LLM Variance**: While the mock mode is deterministic, real-world OpenAI results may vary slightly between runs.
- **Research Prototype**: The goal is to demonstrate the *specialization loop*, not to build a production-grade security scanner.

## Future Work

- **Larger Benchmarks**: Integration with more complex, real-world codebases.
- **Real Tool Integration**: Incorporating static analysis tools like Semgrep or Bandit into the agent's toolkit.
- **Multi-Domain Support**: Expanding beyond security to QA, performance auditing, and deep technical research.
- **Robust Versioning**: Implementing stronger rollback mechanisms and configuration versioning.
- **Autonomous Tool Acquisition**: Allowing the agent to plan, install, and configure its own analysis tools.
- **Cross-Domain Specialization**: Testing how knowledge from one domain can accelerate specialization in another.
