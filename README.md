<p align="center">
  <h1 align="center">codespect-matrix</h1>
  <p align="center"><strong>Multi-Agent Code Evolution Platform</strong></p>
  <p align="center">
    <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
    <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
    <img src="https://img.shields.io/badge/status-stable-brightgreen" alt="Status">
    <img src="https://img.shields.io/badge/agents-16-orange" alt="Agents">
    <img src="https://img.shields.io/badge/tests-82%20passed-success" alt="Tests">
    <img src="https://img.shields.io/badge/coverage-59%25-yellow" alt="Coverage">
  </p>
  <p align="center">
    Multi-Agent · Debate Review · Hybrid Engine · Code Evolution
  </p>
  <p align="center">
    🌐 <a href="README_zh.md">中文</a>
  </p>
</p>

---

## What is codespect-matrix?

> Not just another linter. **codespect-matrix** is a virtual QA team — 16 specialized AI agents that conduct **debate-style code review**, cross-validate every finding, and converge on a final verdict. It learns across projects and gets smarter with every scan.

---

## Why codespect-matrix?

| Traditional QA | codespect-matrix |
|---|---|
| Single-dimension (linter / coverage) | 16 agents in joint debate review |
| Rigid rules, heavy config | AI agents auto-adapt to project characteristics |
| Reports issues without fixes | Every issue includes remediation + auto-fix plan |
| One-and-done scan | **Convergence loop** — repeats until no new findings |
| No CI integration | `--ci` exit code + JSON, ready for GitHub Actions |
| Can't quantify quality changes | `--evolve` health dashboard + `--evolve-baseline` trend tracking |
| Generic, domain-agnostic | Built-in PHI / HIPAA / medical data specialties |
| Starts fresh every time | **Dual memory** — project memory + global knowledge base |

**Flow**: Scan → Agent auto-selection → Parallel inspection → Cross-review → Debate ruling → Convergence → Code Evolution.

---

## Quick Start

```bash
# Install from source
git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
cd codespect-matrix
pip install -e .

# Default multi-agent review
codespect-matrix

# CI gate
codespect-matrix --ci --json

# Code evolution analysis (health dashboard + roadmap)
codespect-matrix --evolve

# Save evolution baseline for trend tracking
codespect-matrix --evolve-baseline

# Full convergence cycle
codespect-matrix --max-rounds 10 --output report.md
```

---

## Architecture

### Agent Roster

| Agent | Engine | Focus |
|---|---|---|
| security | Rule+LLM | Vulnerabilities, injection, weak crypto, secrets |
| healthcare | Rule+LLM | HIPAA compliance, patient data protection |
| phi_protection | Rule+LLM | PHI detection, ID leaks, data masking |
| compliance | Rule+LLM | License compliance, GDPR audit |
| medical_data | Rule+LLM | ICD coding, blood pressure/SpO2 validation |
| developer | Pure LLM | Type safety, error handling, code quality |
| architect | Pure LLM | Circular dependencies, module coupling |
| performance | Pure LLM | N+1 queries, memory bombs, blocking I/O |
| devops | Pure LLM | Observability, health checks, graceful shutdown |
| testing | Pure LLM | Test coverage, testability |
| api | Pure LLM | REST conventions, rate limiting, auth |
| dependency | Pure LLM | Dependency versions, CVE scanning |
| concurrency | Pure LLM | Race conditions, deadlocks, thread safety |
| linter | Subprocess+LLM | Ruff, mypy, flake8 runner with LLM interpretation |
| datascience | Pure LLM | Statistical modeling, data integrity, overfitting detection |
| hardcode | Pure LLM | Hardcoded values, magic numbers, cross-file duplicates |

### 5-Phase Review Workflow

| Phase | Mechanism |
|---|---|
| 0. Select | Project profile + global KB → auto-select 5-8 most relevant agents |
| 1. Inspect | All agents scan in parallel (security/healthcare use rule+LLM dual engine) |
| 2. Review | Each finding cross-validated by agents from different domains |
| 3. Debate | Disputed findings → challenge → defense → Orchestrator ruling |
| 4. Converge | 2 consecutive rounds with no new findings → auto-terminate |

### Code Evolution Dashboard

```bash
codespect-matrix --evolve          # Full evolution analysis
codespect-matrix --evolve-baseline # Save as baseline for trend tracking
```

| Dimension | What It Measures |
|---|---|
| **Health Score** | 0-100 weighted from agent findings (critical×100, high×50, ...) |
| **Technical Debt** | TODO/FIXME/HACK density + oversized files + comment ratio |
| **Architecture** | Import graph → coupling, cycles, God module detection |
| **Test Coverage** | pytest --cov integration + fallback file counting |
| **Evolution Trend** | Baseline comparison → improving / degrading / stable |
| **Roadmap** | P0-P2 prioritized improvement items with effort estimates |

### Self-Evolution Engine

```bash
codespect-matrix --evolve-self     # See what the tool has learned
```

codespect-matrix learns from every QA cycle across projects:

| Phase | What Happens |
|---|---|
| 1. Scan | Run codespect-matrix on a project → findings |
| 2. Fix | Apply remediation → `record_qa_cycle()` captures fixes |
| 3. Re-scan | Verify health improvement → delta tracked |
| 4. Learn | Pattern confidence updated, agent weights adjusted |
| 5. Evolve | `SelfEvolver.evolve()` prunes low-confidence templates, promotes proven patterns to global KB |

Over time, the tool gets more accurate: fewer false positives, faster fix suggestions, better agent selection per project type.

---

## LLM Support

7 provider adapters. Falls back to rule-only mode when no LLM is configured:

| Provider | Config |
|---|---|
| OpenAI (GPT-4o) | `LLM_PROVIDER=openai` |
| Anthropic (Claude) | `LLM_PROVIDER=anthropic` |
| Google (Gemini) | `LLM_PROVIDER=google` |
| Baidu (ERNIE) | `LLM_PROVIDER=baidu` |
| Alibaba (Qwen) | `LLM_PROVIDER=tongyi` |
| Zhipu (GLM) | `LLM_PROVIDER=zhipu` |
| Hugging Face | `LLM_PROVIDER=huggingface` |

---

## Healthcare Specialties

| Check | Details |
|---|---|
| PHI Privacy Scan | Patient info leaks in logs, print, exceptions, exports, APIs |
| Medical Data Validation | Blood pressure (60-260), SpO2 (60-100), ICD-10 format, Chinese ID checksum |
| Data Masking Verification | Name→alias, ID→hash, export without de-identification |

---

## Severity Levels

| Level | Weight | Description |
|------|------|------|
| critical (P0) | 100 | Service crash / PHI leak / build failure |
| high (P1) | 50 | Security vulnerability / data loss / missing HTTP timeout |
| medium (P2) | 15 | Best practice violation / missing rate limiting |
| low (P3) | 3 | Optimization suggestion |

---

## CI/CD Integration (GitHub Actions)

```yaml
- name: codespect-matrix gate
  run: codespect-matrix --ci --json > qa-report.json
```

---

## Python API

```python
# Multi-agent review
from codespect_matrix.agents import AgentOrchestrator

orch = AgentOrchestrator(project_path="/path/to/project")
orch.initialize()
result = orch.run_full_cycle()
print(result["total_findings"], "issues found")

# Code evolution analysis
from codespect_matrix.evolution import EvolutionReporter

reporter = EvolutionReporter(project_path="/path/to/project")
report = reporter.generate_full_report()
print(f"Health: {report['health']['health_score']}/100")
```

```python
# Self-evolution
from codespect_matrix.evolution import SelfEvolver

evolver = SelfEvolver()
evolver.record_qa_cycle(
    project_name="my-app",
    before_health=62.3,
    findings=[...],           # from agent scan
    fixes_applied=[...],      # what was fixed
    after_health=85.1,        # re-scan result
)
evolver.evolve()              # prune weak patterns, promote proven ones
print(evolver.get_evolution_summary())
```

---

## Custom Agents

```python
from codespect_matrix.agents import BaseAgent, AgentRole, Finding

class MyAgent(BaseAgent):
    def get_description(self): return "My custom check"
    def get_domain(self): return "custom"
    
    def inspect(self, files_context):
        return [Finding(
            check_name="my_check",
            severity="medium",
            message="A custom issue detected",
            remediation="Suggested fix",
            confidence=0.8
        )]

# Register and run
from codespect_matrix.agents import AgentOrchestrator
orch = AgentOrchestrator()
orch._add_agent("my_agent", MyAgent(name="my_agent", role=AgentRole.INSPECTOR))
```

---

## CLI Reference

| Flag | Description |
|------|------|
| `--path, -p` | Project path (default: current directory) |
| `--max-rounds` | Max inspection rounds (default: 5) |
| `--ci` | CI/CD gate mode — exit_code=1 when thresholds exceeded |
| `--json` | JSON output |
| `--evolve` | Code evolution analysis — health + debt + architecture + roadmap |
| `--evolve-baseline` | Save evolution analysis as baseline for trend comparison |
| `--evolve-self` | Self-evolution summary — what the tool has learned from past QA cycles |
| `--fix-plan` | AI fix — step 1: generate plan |
| `--fix-execute` | AI fix — step 2: execute |
| `--fix-all` | Execute all fixes including high-risk ones (with `--fix-execute`) |
| `--output` | Report output file path |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -q

# Run tests with coverage
pytest tests/ --cov=codespect_matrix --cov-report=term

# Type checking
mypy codespect_matrix/

# Lint
ruff check codespect_matrix/
```

---

## Free + Donate

codespect-matrix is free and open source. Support the project:
- ⭐ Star this repo
- 💰 [GitHub Sponsors](https://github.com/sponsors/zhouliang-sjtu)

---

## License

MIT License © 2026 Zhou Liang · Shanghai Jiao Tong University School of Medicine

---

**Version**: 1.0.0  
 **Status**: Stable — production-ready  
 **Tests**: 82 passed · 59% coverage  
 **Architecture**: Multi-Agent · Debate Review · Hybrid Engine · Code Evolution
