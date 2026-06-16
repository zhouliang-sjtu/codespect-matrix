# codespect-matrix User Guide

> **Version**: 1.0.0 | **Last Updated**: 2026-06-16  
> Multi-Agent Code Evolution Platform — 16 AI Agents · Debate Review · Hybrid Engine · Health Scoring · Auto-Fix

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
   - [2.1 System Requirements](#21-system-requirements)
   - [2.2 Install from Source](#22-install-from-source)
   - [2.3 Verify Installation](#23-verify-installation)
3. [Configuration](#3-configuration)
   - [3.1 Environment Variables (.env)](#31-environment-variables-env)
   - [3.2 LLM Provider Configuration](#32-llm-provider-configuration)
   - [3.3 No-LLM Mode (Rule-Only Engine)](#33-no-llm-mode-rule-only-engine)
   - [3.4 agent_config.yaml Runtime Parameters](#34-agent_configyaml-runtime-parameters)
4. [Usage Modes](#4-usage-modes)
   - [4.1 Multi-Agent Review Mode (Default)](#41-multi-agent-review-mode-default)
   - [4.2 CI/CD Gate Mode](#42-cicd-gate-mode)
   - [4.3 Code Evolution Analysis](#43-code-evolution-analysis)
   - [4.4 AI Autonomous Fix](#44-ai-autonomous-fix)
   - [4.5 Self-Evolution Summary](#45-self-evolution-summary)
5. [CLI Reference](#5-cli-reference)
6. [Python API](#6-python-api)
   - [6.1 Multi-Agent Review](#61-multi-agent-review)
   - [6.2 Code Evolution Analysis](#62-code-evolution-analysis)
   - [6.3 Self-Evolution Engine](#63-self-evolution-engine)
7. [Output Interpretation](#7-output-interpretation)
   - [7.1 Review Report](#71-review-report)
   - [7.2 Evolution Dashboard](#72-evolution-dashboard)
   - [7.3 CI Gate Output](#73-ci-gate-output)
8. [Advanced Topics](#8-advanced-topics)
   - [8.1 Dual Memory System](#81-dual-memory-system)
   - [8.2 Self-Evolution Engine Explained](#82-self-evolution-engine-explained)
   - [8.3 Healthcare Specialties](#83-healthcare-specialties)
   - [8.4 16 Agent Roles](#84-16-agent-roles)
   - [8.5 Severity Levels & Weights](#85-severity-levels--weights)
9. [Configuration File Reference](#9-configuration-file-reference)
10. [FAQ](#10-faq)

---

## 1. Introduction

**codespect-matrix** is not just another linter. It is a **virtual QA team** — 16 specialized AI agents that conduct **debate-style code review**, cross-validate every finding, converge on a final verdict, and track code health trends over time. It learns across projects and gets smarter with every scan.

### Core Capabilities

| Capability | Description |
|------------|------------|
| Debate Review | 16 agents inspect in parallel → cross-domain review → disputed findings enter debate → Orchestrator ruling |
| Hybrid Engine | Security/healthcare/PHI/compliance use rule+LLM dual engine; others use pure LLM reasoning |
| Dual Memory | Project-level memory (false positive filtering) + Global knowledge base (cross-project learning) |
| Code Evolution | Health scoring · Technical debt · Architecture analysis · Test coverage · Improvement roadmap |
| AI Auto-Fix | Scan → Fix plan → User confirmation → Auto-execute → Re-verify |
| CI/CD Gate | Critical=0 / High≤5 / Medium≤30 thresholds with exit codes |
| Healthcare Specialties | Built-in PHI/HIPAA/medical data validation/data masking |

### Comparison with Traditional QA

| Traditional QA | codespect-matrix |
|---------------|------------------|
| Single-dimension (linter / coverage) | 16 agents in joint debate review |
| Rigid rules, heavy config | AI agents auto-adapt to project characteristics |
| Reports issues without fixes | Every issue includes remediation + auto-fix plan |
| One-and-done scan | **Convergence loop** — repeats until no new findings |
| No CI integration | `--ci` exit code + JSON, ready for CI/CD |
| Can't quantify quality changes | `--evolve` health dashboard + trend tracking |
| Generic, domain-agnostic | Built-in PHI / HIPAA / medical data specialties |

---

## 2. Installation

### 2.1 System Requirements

| Item | Requirement |
|------|------------|
| Python | 3.10, 3.11, or 3.12 |
| Operating System | Windows / macOS / Linux |
| Disk Space | ~200 MB (including dependencies) |
| Optional: LLM API Key | Required for LLM features (see [Section 3.2](#32-llm-provider-configuration)) |

> **No GPU required.** All AI inference is done via cloud APIs. The tool only runs orchestration logic locally.

### 2.2 Install from Source

```bash
# 1. Clone the repository
git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
cd codespect-matrix

# 2. Install (development mode, recommended)
pip install -e .

# 3. Optional: install extra dependencies
pip install -e ".[dev]"         # Dev tools (ruff, mypy, pytest)
pip install -e ".[anthropic]"   # Anthropic Claude support
pip install -e ".[google]"      # Google Gemini support
pip install -e ".[baidu]"       # Baidu ERNIE support
pip install -e ".[tongyi]"      # Alibaba Qwen support
pip install -e ".[zhipu]"       # Zhipu GLM support
pip install -e ".[huggingface]" # HuggingFace local model support
```

> **Note**: After installing an LLM provider's optional dependencies, you must also configure the corresponding API key (see [Section 3.2](#32-llm-provider-configuration)).

### 2.3 Verify Installation

```bash
# Check if CLI is available
codespect-matrix --help

# Quick test on any project directory (no LLM required)
codespect-matrix --path . --max-rounds 1 --json
```

If you see JSON-formatted scan results, the installation is successful.

---

## 3. Configuration

### 3.1 Environment Variables (.env)

Create a `.env` file in the project root (or any code project root):

```bash
# Copy the template
cp .env.example .env
```

**Full .env template**:

```ini
# ==================== LLM Configuration ====================

# LLM Provider (supports: openai, anthropic, google, baidu, tongyi, zhipu, huggingface)
# If not configured, automatically falls back to rule-only engine mode
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1   # Supports custom proxy URLs
OPENAI_MODEL=gpt-4o-mini                     # Recommended: gpt-4o for review, gpt-4o-mini for lightweight tasks
OPENAI_TEMPERATURE=0.7                       # Temperature for generative tasks
OPENAI_MAX_TOKENS=4096

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Google Gemini Configuration
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-pro

# Baidu ERNIE Configuration
BAIDU_API_KEY=your-baidu-api-key
BAIDU_SECRET_KEY=your-baidu-secret-key
BAIDU_MODEL=ERNIE-Bot-4.0

# Alibaba Qwen Configuration
TONGYI_API_KEY=your-tongyi-api-key
TONGYI_MODEL=qwen-plus

# Zhipu GLM Configuration
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_MODEL=glm-4

# Hugging Face Configuration
HUGGINGFACE_API_KEY=your-huggingface-api-key
HUGGINGFACE_MODEL=mistralai/Mistral-7B-v0.3

# ==================== Application Configuration ====================

# Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Max Retries
MAX_RETRIES=3
```

### 3.2 LLM Provider Configuration

codespect-matrix supports **7 LLM providers**, switched via the `LLM_PROVIDER` setting in `.env`:

| Provider | LLM_PROVIDER Value | Extra Dependencies | Recommended Model |
|----------|-------------------|-------------------|-------------------|
| OpenAI | `openai` | None (built-in) | `gpt-4o` (review) / `gpt-4o-mini` (lightweight) |
| Anthropic | `anthropic` | `pip install -e ".[anthropic]"` | `claude-3-sonnet-20240229` |
| Google | `google` | `pip install -e ".[google]"` | `gemini-pro` |
| Baidu | `baidu` | `pip install -e ".[baidu]"` | `ERNIE-Bot-4.0` |
| Alibaba | `tongyi` | `pip install -e ".[tongyi]"` | `qwen-plus` |
| Zhipu | `zhipu` | `pip install -e ".[zhipu]"` | `glm-4` |
| HuggingFace | `huggingface` | `pip install -e ".[huggingface]"` | `mistralai/Mistral-7B-v0.3` |

**Configuration Steps (OpenAI example)**:

1. Set `LLM_PROVIDER=openai` in `.env`
2. Set `OPENAI_API_KEY=sk-xxxx`
3. Optional: Set `OPENAI_API_BASE` for custom proxy
4. Optional: Set `OPENAI_MODEL` to choose model version

**Using a Custom API Proxy**:

```ini
# For third-party proxies or Azure OpenAI
OPENAI_API_BASE=https://your-proxy.com/v1
OPENAI_API_KEY=your-key
```

### 3.3 No-LLM Mode (Rule-Only Engine)

**codespect-matrix can run without any LLM configured.** In this mode:

- **Rule engine agents** (SecurityAgent, HealthcareAgent, PHIAgent, ComplianceAgent, MedicalDataAgent) still work normally, using built-in rule scans
- **Pure LLM agents** (DeveloperAgent, ArchitectAgent, PerformanceAgent, etc.) are skipped
- Reviews are still effective, but the number and depth of findings may be lower than LLM mode

**Configuring rule-only mode**:

Simply leave all LLM-related configurations out of `.env`. The system detects this and falls back automatically.

You can also explicitly set it in `agent_config.yaml`:

```yaml
engine:
  llm_unavailable: rule_only   # Options: rule_only | skip | error
```

### 3.4 agent_config.yaml Runtime Parameters

The `agent_config.yaml` in the project root controls runtime behavior. You can copy this file to a target project directory to override defaults.

```yaml
# Agent Selection Strategy
agent_selection:
  strategy: auto              # auto | profile_matching | fixed_list
  min_compatibility: 0.3      # Minimum compatibility for profile_matching strategy
  max_active: 8               # Maximum active agents per round

# Inspection Phase
inspection:
  max_context_tokens: 12000   # Maximum file context tokens sent to LLM
  timeout_per_agent: 120      # Timeout per agent (seconds)
  retry_count: 2              # LLM call retry count on failure

# Cross-Review Phase
review:
  min_reviewers: 2            # Minimum reviewers per finding (from different domains)
  confirm_threshold: 0.75     # Confidence threshold for "confirmed" verdict
  disagreement_threshold: 0.35 # Disagreement threshold triggering debate

# Debate Phase
debate:
  max_rounds: 3               # Maximum debate rounds per finding
  arbiter_threshold: 0.8      # Arbiter confidence threshold to close debate
  round_timeout: 90           # Timeout per debate round (seconds)

# Convergence Control
convergence:
  max_rounds: 5               # Maximum overall inspection rounds
  stability_threshold: 2      # Consecutive rounds with no new findings before auto-stop

# Fix Engine
fix:
  auto_backup: true           # Auto-backup files before modification
  backup_dir: ".codespect_matrix_backups"
  require_confirmation: true  # Require user confirmation before executing fixes
  max_files_per_session: 20   # Max files to fix in a single session

# CI Gate Thresholds
ci_gate:
  max_critical: 0
  max_high: 5
  max_medium: 30

# Engine Fallback
engine:
  llm_unavailable: rule_only
  analysis_temperature: 0.2
  default_model: "gpt-4o"
```

---

## 4. Usage Modes

codespect-matrix provides **5 main usage modes**, triggered by different CLI flags.

### 4.1 Multi-Agent Review Mode (Default)

The most comprehensive review mode, executing all 5 phases:

1. **Agent Selection** — Auto-select 5-8 most relevant agents based on project profile
2. **Parallel Inspection** — All selected agents scan source code simultaneously
3. **Cross-Review** — Each finding cross-validated by agents from different domains
4. **Debate Ruling** — Disputed findings enter debate, Orchestrator delivers final verdict
5. **Convergence Loop** — Repeat inspection until 2 consecutive rounds with no new findings

#### Basic Usage

```bash
# Review current directory
codespect-matrix

# Target a specific project
codespect-matrix --path /home/user/my-project

# Use relative path
codespect-matrix -p ../my-python-app
```

#### Controlling Review Rounds

```bash
# Quick scan (1 round)
codespect-matrix --max-rounds 1

# Deep review (10 rounds)
codespect-matrix --max-rounds 10
```

> **Tip**: The convergence mechanism auto-terminates. Setting a large `--max-rounds` only sets an upper bound. The review stops automatically after 2 consecutive rounds with no new findings.

#### Output Format

```bash
# JSON output (for programmatic processing)
codespect-matrix --json

# Save report to file
codespect-matrix --output report.md

# JSON output and save file simultaneously
codespect-matrix --json --output report.json
```

#### Sample Review Output

```
======================================================================
  codespect-matrix — 16-Agent Code Evolution Platform
  Review · Debate · Converge · Evolve
======================================================================

  project: Backend
  domain: medical
  scale: medium
  7 agents active:
    [security       ] security — Vulnerability scanning, crypto strength audit...
    [healthcare     ] healthcare — HIPAA compliance, patient data protection
    [code_quality   ] developer — Code quality, type safety, error handling...
    [architecture   ] architect — Circular dependency, module coupling...
    [performance    ] performance — N+1 queries, memory bombs, blocking I/O...
    [testing        ] testing — Test coverage, testability...
    [api            ] api — REST conventions, rate limiting, auth...

  starting review...

  === ROUND 1 ===
  Inspecting... 7 agents scanned, 23 findings
  Reviewing... cross-validated by different-domain agents
  Ruling: 15 confirmed, 5 rejected, 3 disputed

  === ROUND 2 ===
  Debate closed: 3 disputed → 2 confirmed, 1 rejected
  Inspecting... 7 agents scanned, 2 new findings
  Converged: 2 consecutive rounds with no new findings

  ============================================================
  REVIEW SUMMARY
  ============================================================
  Total findings:    25
  Confirmed:         17
  Rejected:          6
  Adjusted:          2
  Rounds:            2
  Converged:         yes

  Critical: 1
    - phi_protection_patient_id_leak: Patient ID found in log output
      File: src/api/patient_export.py:42
      Fix: Use masked_patient_id() before logging

  High: 3
    - security_eval_injection: eval() with user-controlled input
      File: src/utils/dynamic_query.py:18
      Fix: Use ast.literal_eval() or safe parser
    ...
```

### 4.2 CI/CD Gate Mode

Used to integrate code review into CI/CD pipelines. Determines whether code quality passes predefined thresholds.

#### Default Thresholds

| Level | Max Allowed |
|-------|------------|
| Critical (P0) | 0 |
| High (P1) | 5 |
| Medium (P2) | 30 |

Thresholds can be customized in `agent_config.yaml` under the `ci_gate` section.

#### Basic Usage

```bash
# CI gate check (exit code indicates result)
codespect-matrix --ci

# JSON output (CI tool friendly)
codespect-matrix --ci --json > qa-report.json
```

#### Exit Codes

| Exit Code | Meaning |
|-----------|---------|
| `0` | Pass — all severity counts within thresholds |
| `1` | Fail — at least one severity exceeded threshold |

#### CI Output Example

```
============================================================
CI Gate Check — FAIL
============================================================
severities: {'critical': 0, 'high': 6, 'medium': 12}
confirmed: 18
rejected: 7
gate: FAIL
```

#### GitHub Actions Integration

```yaml
name: Code Quality Gate

on:
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install codespect-matrix
        run: |
          git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
          cd codespect-matrix && pip install -e .

      - name: Run Quality Gate
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd ${{ github.workspace }}/your-project
          codespect-matrix --ci --json --path . > codespect-report.json

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: codespect-report
          path: codespect-report.json
```

#### GitLab CI Integration

```yaml
# .gitlab-ci.yml
quality-gate:
  image: python:3.11
  stage: test
  before_script:
    - git clone https://github.com/zhouliang-sjtu/codespect-matrix.git /tmp/codespect
    - cd /tmp/codespect && pip install -e .
  script:
    - cd $CI_PROJECT_DIR
    - codespect-matrix --ci --json --path . > codespect-report.json
  artifacts:
    when: always
    paths:
      - codespect-report.json
```

### 4.3 Code Evolution Analysis

Perform comprehensive code evolution analysis, generating a health dashboard, technical debt report, architecture analysis, and improvement roadmap.

#### Basic Usage

```bash
# Full evolution analysis (health + debt + architecture + roadmap)
codespect-matrix --evolve

# Save evolution baseline (for later trend comparison)
codespect-matrix --evolve-baseline

# Compare trend (if baseline exists, auto-compares)
codespect-matrix --evolve

# JSON output format
codespect-matrix --evolve --json
```

#### Evolution Dashboard Output

```
----------------------------------------------------------------------
PROJECT HEALTH DASHBOARD
----------------------------------------------------------------------
  Overall Health       OK [########################------]  80.5%
    Code Quality       OK [########################------]  78.0%
    Architecture       OK [#########################-----]  82.3%
    Debt Freedom       OK [########################------]  79.0%
    Test Coverage      ~~ [##############----------------]  45.0%

  CODE QUALITY [GOOD]
    score: 78.0/100
    high: 3
    medium: 12
    low: 5

  TECHNICAL DEBT [MODERATE]
    index: 35/100
    markers: 8
      [TODO] Refactor patient data export module...
      [FIXME] Race condition when concurrent write...
    large files: 2
      src/api/handler.py (1234 lines)
      src/models/database.py (892 lines)

  ARCHITECTURE [CLEAN]
    health: 82.3/100
    modules: 24
    cycles: 0
    god modules: 1
      src/api/handler.py (1234 lines, fan-out: 18)

  TEST COVERAGE [MODERATE]
    coverage: 45.0%
    lines: 890/1978

  ------------------------------------------------------------
  IMPROVEMENT ROADMAP
  ------------------------------------------------------------
  [P1] technical_debt
       Resolve 8 TODO/FIXME/HACK markers
       reason: Debt index 35/100
       effort: 4h estimated

  [P1] architecture
       Refactor 1 God modules
       reason: src/api/handler.py
       effort: 2-4h per module

  [P2] technical_debt
       Split 2 oversized files (>500 lines)
       reason: Large files: src/api/handler.py, src/models/database.py
       effort: 4h estimated

  [P2] testing
       Increase test coverage to 50%+
       reason: Current coverage: 45.0%
       effort: depends on project size
```

#### Evolution Trend Comparison

After first running `--evolve-baseline`, subsequent `--evolve` runs auto-compare:

```
  Evolution Trend — IMPROVING
    Health:  78.0 → 82.5 (+4.5)
    Debt:    35 → 28 (-7)
    Findings: 25 → 18 (-7)
```

### 4.4 AI Autonomous Fix

Two-step AI fix workflow: generate a fix plan for review, then execute after confirmation.

#### Step 1: Generate Fix Plan

```bash
# Scan project and generate fix plan (preview only, no code changes)
codespect-matrix --fix-plan
```

Sample output:

```
  ============================================================
  codespect-matrix — AI Autonomous Fix: Generate Plan
  ============================================================

  Health score (before): 62.0/100
  Confirmed issues:     17
  Auto-fixable:         12
  Needs manual review:  5

  Auto-fixable issues:
  ----------------------------------------------------
  [H] security_eval_injection
       eval() with user-controlled input in dynamic_query
       src/utils/dynamic_query.py:18
       fix: Replace eval() with ast.literal_eval() for safe parsing

  [M] developer_missing_timeout
       HTTP request without timeout parameter
       src/api/client.py:45
       fix: Add timeout=30 parameter to requests.get() call
  ...

  To apply auto-fixes:   codespect-matrix --fix-execute
  To apply ALL fixes:    codespect-matrix --fix-execute --fix-all
  (backups saved to .codespect_matrix_backups/)
```

#### Step 2: Execute Fixes

```bash
# Execute only safe fixes (can_auto_fix=true items)
codespect-matrix --fix-execute

# Execute all fixes including high-risk ones
codespect-matrix --fix-execute --fix-all
```

After execution, the tool automatically:

1. **Backs up originals** → `.codespect_matrix_backups/` directory
2. **Applies fixes** → LLM generates precise old_str/new_str patches
3. **Re-scans to verify** → Confirms health score improvement
4. **Records to SelfEvolver** → For future learning

Sample output:

```
  Health before fix:  62.0/100
  Issues to address:  17

  Fix results:
    Applied:  12
    Failed:   0

  Files modified:
    - src/utils/dynamic_query.py
    - src/api/client.py
    ...

  Backups saved to: .codespect_matrix_backups/

  Re-scanning to verify...
  Health after fix:   78.5/100
  Improvement:        +16.5
  SelfEvolver:        cycle recorded for future learning
```

> **Safety Note**: The fix engine automatically backs up modified files to `.codespect_matrix_backups/`. If the fix results are unsatisfactory, you can restore from backups.

#### Rolling Back Fixes

```bash
# Restore all modified files from backup directory
cp -r .codespect_matrix_backups/* .
```

### 4.5 Self-Evolution Summary

View what the tool has learned from historical QA cycles.

```bash
codespect-matrix --evolve-self
```

Sample output:

```
  ============================================================
  codespect-matrix — Self-Evolution Summary
  ============================================================

  Generation:        3
  QA Cycles:         47
  Projects Helped:   8
  Avg Health Gain:   +15.3%
  Patterns Learned:  23

  Top Agents:
    1. security (accuracy: 92%)
    2. developer (accuracy: 88%)
    3. phi_protection (accuracy: 95%)

  Fix Confidence by Issue Type:
    eval_injection          [####################] 95% (12 attempts)
    missing_timeout         [################    ] 80% (8 attempts)
    hardcoded_secret        [####################] 100% (5 attempts)
    ...
```

---

## 5. CLI Reference

| Argument | Short | Type | Default | Description |
|----------|-------|------|---------|-------------|
| `--path` | `-p` | string | `.` | Project path (absolute or relative) |
| `--max-rounds` | — | int | `5` | Maximum review rounds |
| `--ci` | — | flag | — | CI/CD gate mode (exit code indicates result) |
| `--json` | — | flag | — | Output in JSON format |
| `--output` | — | string | — | Report output file path |
| `--evolve` | — | flag | — | Code evolution analysis (health dashboard + roadmap) |
| `--evolve-baseline` | — | flag | — | Save evolution baseline for trend comparison |
| `--evolve-self` | — | flag | — | Self-evolution summary — what the tool has learned |
| `--fix-plan` | — | flag | — | AI fix step 1: generate fix plan |
| `--fix-execute` | — | flag | — | AI fix step 2: execute fixes |
| `--fix-all` | — | flag | — | With `--fix-execute`, include high-risk fixes |

### Common Command Combinations

```bash
# === Daily Review ===
codespect-matrix                                              # Default review
codespect-matrix -p /path/to/project --max-rounds 3           # Target project, 3 rounds
codespect-matrix --json --output report.json                  # JSON output and save

# === CI/CD ===
codespect-matrix --ci --json                                  # CI gate
codespect-matrix --ci --json > qa-report.json                 # CI gate + save report

# === Evolution Analysis ===
codespect-matrix --evolve                                     # Health dashboard
codespect-matrix --evolve-baseline                            # Save baseline
codespect-matrix --evolve --evolve-baseline                   # Analyze and save baseline

# === AI Fix ===
codespect-matrix --fix-plan                                   # Generate plan
codespect-matrix --fix-execute                                # Execute safe fixes
codespect-matrix --fix-execute --fix-all                      # Execute all fixes

# === Learning Feedback ===
codespect-matrix --evolve-self                                # View tool evolution status
codespect-matrix --evolve-self --json                         # JSON format evolution status
```

---

## 6. Python API

If you need to integrate codespect-matrix in Python scripts, use the Python API.

### 6.1 Multi-Agent Review

```python
from codespect_matrix.agents import AgentOrchestrator

# Initialize orchestrator
orch = AgentOrchestrator(project_path="/path/to/project")

# Initialize: analyze project + select agents
orch.initialize()

# Run full review cycle
result = orch.run_full_cycle(max_rounds=5)

# View results
print(f"Total findings: {result['total_findings']}")
print(f"Confirmed: {len(result['confirmed_issues'])}")
print(f"Rejected: {len(result['rejected_issues'])}")
print(f"Converged: {result['converged']}")

# Iterate through confirmed issues
for issue in result['confirmed_issues']:
    print(f"[{issue['severity']}] {issue['check_name']}: {issue['message']}")

# Generate readable report
report = orch.generate_report(result)
print(report)
```

### 6.2 Code Evolution Analysis

```python
from codespect_matrix.evolution import (
    EvolutionReporter,
    EvolutionBaseline,
    HealthScorer,
    TechDebtAnalyzer,
    ArchitectureAnalyzer,
    TestCoverageEstimator,
)

project_path = "/path/to/project"

# Method 1: Use EvolutionReporter for full report
reporter = EvolutionReporter(project_path)

# If you have agent review results
findings = [
    {"check_name": "security_eval", "severity": "critical", "message": "eval() injection"},
    {"check_name": "developer_timeout", "severity": "high", "message": "missing timeout"},
]

report = reporter.full_report(agent_findings=findings)
print(f"Health Score: {report['health']['health_score']}/100")
print(f"Overall: {report['overall_score']}/100 ({report['overall_level']})")
print(f"Technical Debt: {report['technical_debt']['debt_index']}/100")
print(f"Architecture: {report['architecture']['architecture_health']}/100")

# Method 2: Use individual analyzers independently
health = HealthScorer().compute(findings)
debt = TechDebtAnalyzer().analyze(project_path)
arch = ArchitectureAnalyzer().analyze(project_path)
coverage = TestCoverageEstimator().estimate(project_path)

# Save and load baselines
baseline = EvolutionBaseline(project_path)
baseline.save(report)            # Save current state as baseline

# Later: load and compare
previous = baseline.load()
if previous:
    delta = baseline.diff(report)  # Current vs baseline
    print(f"Trend: {delta['trend']}")
    print(f"Health delta: {delta['health_delta']:+.1f}")
```

### 6.3 Self-Evolution Engine

```python
from codespect_matrix.evolution import SelfEvolver

evolver = SelfEvolver()

# Record a QA cycle
evolver.record_qa_cycle(
    project_name="my-app",
    before_health=62.3,
    findings=[
        {"check_name": "security_eval", "severity": "critical", "message": "eval() used"},
        {"check_name": "developer_timeout", "severity": "high", "message": "no timeout"},
    ],
    fixes_applied=[
        {"check_name": "security_eval", "success": True},
        {"check_name": "developer_timeout", "success": True},
    ],
    after_health=85.1,
    fix_details=[
        {
            "check_name": "security_eval",
            "reasoning": "Replaced eval() with ast.literal_eval()",
            "old_code": "return eval(user_input)",
            "new_code": "return ast.literal_eval(user_input)",
        },
    ],
)

# Trigger evolution: prune low-confidence patterns, promote proven ones
evolver.evolve()

# View evolution summary
summary = evolver.get_evolution_summary()
print(f"Generation: {summary['generation']}")
print(f"Total Cycles: {summary['total_cycles']}")
print(f"Avg Health Gain: {summary['average_health_improvement']}%")
```

---

## 7. Output Interpretation

### 7.1 Review Report

Multi-agent review output contains the following key sections:

| Section | Description |
|---------|------------|
| **Project Info** | Project type, domain, scale, active agent list |
| **Round Results** | Findings per round, confirmed, rejected counts |
| **Review Summary** | Total findings, confirmed, rejected, adjusted |
| **Issue Detail** | Each confirmed issue: severity, description, file location, remediation |

**Severity markers**:
- `[C]` Critical (P0) — Must fix immediately, may cause crash/data leak
- `[H]` High (P1) — Fix soon, security vulnerability/data loss
- `[M]` Medium (P2) — Should fix, best practice violation
- `[L]` Low (P3) — Optimization suggestion

### 7.2 Evolution Dashboard

| Metric | Range | Excellent | Good | Fair | Poor | Critical |
|--------|-------|-----------|------|------|------|----------|
| Overall Health | 0-100 | ≥85 | ≥70 | ≥50 | ≥30 | <30 |
| Code Quality | 0-100 | ≥90 | ≥70 | ≥50 | ≥30 | <30 |
| Architecture | 0-100 | ≥80 | ≥60 | ≥40 | — | <40 |
| Debt Freedom | 0-100 | ≥80 | ≥70 | ≥50 | — | <50 |
| Test Coverage | 0-100% | ≥80% | ≥50% | >0% | — | 0% |

**Technical Debt Index**:
- 0-19: Low — Clean codebase
- 20-49: Moderate — Some markers to address
- 50-79: High — Significant accumulation, prioritize
- 80-100: Critical — Severe maintainability issues

### 7.3 CI Gate Output

```json
{
  "exit_code": 1,
  "severities": {
    "critical": 0,
    "high": 6,
    "medium": 12
  },
  "total_findings": 25,
  "confirmed": 18,
  "rejected": 7,
  "converged": false,
  "timestamp": "2026-06-16T10:30:00Z"
}
```

| Field | Description |
|-------|------------|
| `exit_code` | 0=pass, 1=fail |
| `severities.critical` | Critical issue count (threshold: 0) |
| `severities.high` | High issue count (threshold: ≤5) |
| `severities.medium` | Medium issue count (threshold: ≤30) |
| `total_findings` | Total findings from all agents (includes duplicates) |
| `confirmed` | Issues confirmed by cross-review |
| `rejected` | Issues rejected by cross-review |
| `converged` | Whether converged within 1 round |
| `timestamp` | Review timestamp |

---

## 8. Advanced Topics

### 8.1 Dual Memory System

codespect-matrix has a dual-layer memory system that continuously improves review quality through cross-project and cross-session knowledge accumulation.

#### Project-Level Memory

Stored in each project root as `.codespect_matrix_agent_memory.json`:

- **False Positive Records**: Issues confirmed as non-issues, auto-filtered in future scans
- **Scan History**: Findings count and health score changes from past reviews
- **Convergence Tracking**: Conclusions confirmed through multi-round debate

```json
// .codespect_matrix_agent_memory.json example structure
{
  "false_positives": [
    {"check_name": "security_eval_injection", "message": "...", "confirmed_fp": true}
  ],
  "scan_history": [
    {"timestamp": "2026-06-15", "findings": 25, "confirmed": 17}
  ],
  "convergence_records": {}
}
```

#### Global Knowledge Base

Stored in `~/.codespect_matrix_knowledge/` directory, shared across all projects:

- **Cross-Project False Positive Library**: Checks that trigger false alarms across all your projects
- **Agent Recommendation Weights**: Most effective agents for similar project types, based on historical results
- **Fix Pattern Library**: Successfully applied code fix patterns for future reference
- **Self-Evolution Data**: Experience accumulated from QA cycles (see [Section 8.2](#82-self-evolution-engine-explained))

```bash
# View global knowledge base location
ls ~/.codespect_matrix_knowledge/

# Manually clear global knowledge base (reset learning state)
rm -rf ~/.codespect_matrix_knowledge/
```

### 8.2 Self-Evolution Engine Explained

SelfEvolver is codespect-matrix's core differentiation feature, enabling the tool to continuously learn from each QA cycle.

#### Evolution Loop

```
   ┌──────────────────────────────────────────────────┐
   │                                                  │
   ▼                                                  │
┌──────┐   ┌──────┐   ┌──────────┐   ┌──────┐   ┌──────┐
│Scan  │──▶│Fix   │──▶│Re-scan   │──▶│Learn │──▶│Evolve│
│      │   │Apply │   │Verify    │   │Update│   │Prune │
└──────┘   └──────┘   └──────────┘   └──────┘   └──────┘
                                                │
                                                ▼
                                         ┌──────────┐
                                         │Global KB │
                                         │Updated   │
                                         └──────────┘
```

#### Evolution Process

| Phase | Action | Effect |
|-------|--------|--------|
| Scan | Run codespect-matrix review | Discover n issues |
| Fix | Apply fixes (manual or `--fix-execute`) | Fix m issues |
| Re-scan | Review again to verify | Health score A → B |
| Learn | record_qa_cycle() records | Update fix pattern confidence |
| Evolve | evolve() prunes and optimizes | Low-confidence templates downgraded, proven patterns promoted to global KB |

#### Long-Term Effects

The more projects you review, fix, and re-scan with codespect-matrix, the tool becomes:

- **Fewer False Positives**: Automatically learns which patterns are not issues in your codebase
- **Faster Detection**: Recommends the best agents based on historical effectiveness
- **More Accurate Fixes**: Successfully applied patterns get high-confidence fix recommendations
- **Smarter Selection**: New projects automatically get the best agent combination based on similar project experience

### 8.3 Healthcare Specialties

codespect-matrix includes built-in specialized checks for healthcare/medical domains:

| Check | Trigger | Detection |
|-------|---------|-----------|
| **PHI Privacy Scan** | Domain identified as "medical" | Patient info leaks in logs, print, exceptions, exports, API responses |
| **Medical Data Validation** | Same as above | Blood pressure range (60-260), SpO2 range (60-100), ICD-10 format, Chinese ID checksum |
| **Data Masking Verification** | Same as above | Name→alias, ID→hash, export without de-identification |
| **HIPAA Compliance** | Same as above | Missing audit logs, unencrypted data transmission, insufficient access control |

These are executed by dedicated agents:
- **PHIAgent** (`phi_protection`): PHI/PII data leak detection
- **HealthcareAgent** (`healthcare`): HIPAA compliance audit
- **MedicalDataAgent** (`medical_data`): Medical data format and range validation
- **ComplianceAgent** (`compliance`): License compliance, GDPR audit

### 8.4 16 Agent Roles

| Agent ID | Name | Engine Type | Focus Area |
|----------|------|-------------|------------|
| `security` | SecurityAgent | Rule+LLM | Vulnerability scanning, weak crypto, hardcoded secrets, unsafe deserialization |
| `healthcare` | HealthcareAgent | Rule+LLM | HIPAA compliance, patient data protection, access control audit |
| `phi_protection` | PHIAgent | Rule+LLM | PHI/PII detection, ID number leaks, log data masking |
| `compliance` | ComplianceAgent | Rule+LLM | License compliance, GDPR audit, audit log integrity |
| `medical_data` | MedicalDataAgent | Rule+LLM | ICD-10 coding, blood pressure/SpO2 ranges, Chinese ID validation |
| `developer` | DeveloperAgent | Pure LLM | Type safety, error handling, function complexity, naming conventions |
| `architect` | ArchitectAgent | Pure LLM | Circular dependency detection, module coupling, God module identification |
| `performance` | PerformanceAgent | Pure LLM | N+1 queries, memory leaks, blocking I/O, large object allocation |
| `devops` | DevopsAgent | Pure LLM | Observability, health checks, graceful shutdown, resource limits |
| `testing` | TestingAgent | Pure LLM | Test coverage, testability, mock usage, assertion quality |
| `api` | APIAgent | Pure LLM | REST conventions, rate limiting, authentication, error response format |
| `dependency` | DependencyAgent | Pure LLM | Dependency version checks, CVE scanning, outdated package detection |
| `concurrency` | ConcurrencyAgent | Pure LLM | Race conditions, deadlock detection, thread safety, async patterns |
| `linter` | LinterAgent | Subprocess+LLM | Ruff/mypy/flake8 runner with LLM interpretation |
| `datascience` | DataScienceAgent | Pure LLM | Statistical modeling correctness, data integrity, overfitting detection |
| `hardcode` | HardcodeAgent | Pure LLM | Hardcoded values, magic numbers, cross-file duplicate values |

### 8.5 Severity Levels & Weights

In health score calculation, different severities use different weights:

| Level | Label | Weight | Description | Example |
|-------|-------|--------|-------------|---------|
| Critical | P0 | ×100 | Service crash / PHI leak / build failure | `eval()` injection, patient ID in plaintext log |
| High | P1 | ×50 | Security vulnerability / data loss / missing timeout | Hardcoded secret, HTTP request without timeout |
| Medium | P2 | ×15 | Best practice violation / missing rate limit | Missing rate limiting, TODO buildup |
| Low | P3 | ×3 | Optimization suggestion | Naming improvement, code style |

**Health Score Formula**:

```
raw_score = Σ(severity_weight × count_per_severity)
max_score = Σ(severity_weight × 10)    # baseline: 10 per severity level
health = max(0, 100 - (raw_score / max_score) × 100)
```

---

## 9. Configuration File Reference

### agent_config.yaml Defaults

```yaml
# ─── Agent Selection ───────────────────────────
agent_selection:
  strategy: auto
  min_compatibility: 0.3
  max_active: 8

# ─── Inspection ────────────────────────────────
inspection:
  max_context_tokens: 12000
  timeout_per_agent: 120
  retry_count: 2

# ─── Cross-Review ──────────────────────────────
review:
  min_reviewers: 2
  confirm_threshold: 0.75
  disagreement_threshold: 0.35

# ─── Debate ────────────────────────────────────
debate:
  max_rounds: 3
  arbiter_threshold: 0.8
  round_timeout: 90

# ─── Convergence ───────────────────────────────
convergence:
  max_rounds: 5
  stability_threshold: 2

# ─── Fix Engine ────────────────────────────────
fix:
  auto_backup: true
  backup_dir: ".codespect_matrix_backups"
  require_confirmation: true
  max_files_per_session: 20

# ─── Memory System ─────────────────────────────
memory:
  project_memory: true
  project_memory_file: ".codespect_matrix_agent_memory.json"
  global_knowledge: true
  global_kb_dir: "~/.codespect_matrix_knowledge/"

# ─── CI Gate ───────────────────────────────────
ci_gate:
  max_critical: 0
  max_high: 5
  max_medium: 30

# ─── Engine Fallback ───────────────────────────
engine:
  llm_unavailable: rule_only
  analysis_temperature: 0.2
  default_model: "gpt-4o"
```

### Files Generated by the Tool

After running codespect-matrix, the following files may appear in your project directory:

| File | Purpose | Recommendation |
|------|---------|---------------|
| `.codespect_matrix_agent_memory.json` | Project-level memory | Commit to Git |
| `.codespect_matrix_backups/` | Pre-fix backups | Delete after verifying fixes |
| `.codespect_matrix_evolution_baseline.json` | Evolution baseline | Commit to Git |
| `~/.codespect_matrix_knowledge/` | Global knowledge base | Do not commit, keep locally |

---

## 10. FAQ

### Q1: Can I use it without an LLM?

**Yes.** codespect-matrix supports pure rule engine mode. Without LLM configuration:
- Rule engine agents (security, healthcare, phi_protection, compliance, medical_data) still work
- Pure LLM agents are automatically skipped
- Review scope is reduced but still effective

### Q2: Which programming languages are supported?

Currently optimized primarily for **Python** projects. Other language projects can run evolution analysis (technical debt and architecture analysis are Python-only), but rule engine agents in multi-agent review may not parse correctly.

### Q3: How much do LLM API calls cost?

- Using `gpt-4o-mini` to review a medium project (~5000 lines) consumes approximately **5-15K tokens**, very low cost
- Using `gpt-4o` for a full review consumes approximately **15-40K tokens**
- Recommended: use `gpt-4o-mini` for daily use, `gpt-4o` for important reviews

### Q4: How long does a review take?

- Small project (<1000 lines): **~10-30 seconds**
- Medium project (1000-10000 lines): **~30-120 seconds**
- Large project (>10000 lines): **~2-5 minutes**
- Time is primarily affected by LLM API response speed

### Q5: How do I run only specific agents?

Agents are auto-selected by default. To control selection:
1. Set `agent_selection.max_active` in `agent_config.yaml` to limit quantity
2. Or use the Python API to manually specify:

```python
from codespect_matrix.agents import AgentOrchestrator

orch = AgentOrchestrator(project_path=".")
orch._register_all_agents()

# Manually select agents
orch.active_agents = ["security", "developer", "linter"]
orch.run_full_cycle()
```

### Q6: Is the auto-fix feature safe?

The fix engine is designed with safety as a priority:

1. **Auto-backup**: Every modified file is backed up to `.codespect_matrix_backups/` first
2. **User Confirmation**: Default requires reviewing `--fix-plan` before `--fix-execute`
3. **Safe Fixes First**: Items marked `can_auto_fix=true` (adding timeout params, replacing unsafe functions)
4. **Fuzzy Matching**: If the LLM-generated patch fails exact match, it attempts context-based fuzzy matching
5. **Rollback Available**: Restore directly from the backup directory

### Q7: When should I update the evolution baseline?

Recommended at these milestones:

- After each release: `codespect-matrix --evolve-baseline`
- Before/after major refactoring: save pre-refactor baseline, compare after
- Periodically (e.g., monthly): track project health trends

### Q8: How do I use it across multiple projects?

```bash
# Use independently per project
cd /path/to/project-a
codespect-matrix --evolve

cd /path/to/project-b
codespect-matrix --evolve

# Python API batch processing
import os
from codespect_matrix.agents import AgentOrchestrator

projects = ["/path/to/a", "/path/to/b", "/path/to/c"]
for p in projects:
    orch = AgentOrchestrator(project_path=p)
    orch.initialize()
    result = orch.run_full_cycle(max_rounds=3)
    print(f"{os.path.basename(p)}: {len(result['confirmed_issues'])} issues")
```

### Q9: What is convergence and why is it important?

Convergence means 2 consecutive inspection rounds yield no new findings. This indicates that, under the current agent configuration, all discoverable issues have been exposed. The convergence mechanism ensures:

- No infinite scanning loops
- A clear termination condition for reviews
- Completeness of results (from the current perspective)

### Q10: Can I add custom rules?

Built-in agents use predefined check logic (rule engine) and LLM prompts (LLM agents). For customization:

1. **Adjust thresholds**: Modify review/debate parameters in `agent_config.yaml`
2. **Add false positive filtering**: Mark known false positives in `.codespect_matrix_agent_memory.json`
3. **Extend agents**: Register custom agents via Python API (requires development)

---

## Appendix: Project File Structure

```
codespect-matrix/
├── codespect_matrix/            # Core code
│   ├── agents/                  # Agent system
│   │   ├── base.py              # Agent base classes and data types
│   │   ├── rule_agents.py       # Rule+LLM hybrid agents (security/healthcare/PHI)
│   │   ├── llm_agents.py        # Pure LLM agents (developer/architecture/performance, etc.)
│   │   ├── orchestrator.py      # Orchestrator — multi-agent coordination, review workflow
│   │   ├── bus.py               # Inter-agent communication bus
│   │   └── memory.py            # Dual memory system
│   ├── cli.py                   # CLI entry point
│   ├── core.py                  # Core service
│   ├── scanner.py               # Project profile scanner
│   ├── llm_service.py           # LLM service wrapper (7 providers)
│   ├── fix_engine.py            # AI fix engine
│   ├── evolution.py             # Evolution engine (health/debt/architecture/self-evolution)
│   └── models.py                # Data models
├── locales/                     # Internationalization
│   ├── zh/messages.json         # Chinese messages
│   └── en/messages.json         # English messages
├── tests/                       # Tests
├── agent_config.yaml            # Agent runtime configuration (defaults)
├── .env.example                 # Environment variable template
├── pyproject.toml               # Project metadata and dependencies
├── README.md                    # Project overview (English)
├── README_zh.md                 # Project overview (Chinese)
├── USER_GUIDE_zh.md             # User Guide (Chinese) ← this file
├── USER_GUIDE_en.md             # User Guide (English)
└── LICENSE                      # MIT License
```

---

> **Support**: https://github.com/zhouliang-sjtu/codespect-matrix/issues  
> **Homepage**: https://github.com/zhouliang-sjtu/codespect-matrix
