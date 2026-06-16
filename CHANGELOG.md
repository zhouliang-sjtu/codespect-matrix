# Changelog

All notable changes to codespect-matrix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-16

### Added
- 16-agent multi-agent architecture: SecurityAgent, HealthcareAgent, PHIAgent, DeveloperAgent, ArchitectAgent, PerformanceAgent, DevOpsAgent, TestAgent, APIAgent, DependencyAgent, ConcurrencyAgent, LinterAgent, DatascienceAgent, HardcodeAgent, ComplianceAgent, MedicalDataAgent
- Debate-style review workflow: Inspect → Cross-review → Debate → Converge → Fix
- Hybrid engine: Rule+LLM for security/healthcare/PHI/compliance; pure LLM for others
- Dual memory: ProjectMemory (`.codespect_matrix_agent_memory.json`) + GlobalKnowledgeBase (`~/.codespect_matrix_knowledge/`)
- Agent communication bus with broadcast/point-to-point messaging
- AI autonomous fix: `--fix-plan` → `--fix-execute` two-step workflow
- **Code Evolution Platform**: 6 engines — HealthScorer, TechDebtAnalyzer, ArchitectureAnalyzer, TestCoverageEstimator, EvolutionReporter, EvolutionBaseline
- **Self-Evolution Engine (SelfEvolver)**: Learns from QA → Fix → Re-QA cycles across projects. Tracks fix effectiveness per check, agent performance by severity, fix confidence scoring, and automatic pattern promotion/pruning
- `--evolve` / `--evolve-baseline` / `--evolve-self` CLI flags
- `--ci` / `--json` CLI flags for CI/CD gate mode
- `agent_config.yaml` runtime configuration
- `locales/{en,zh}/messages.json` i18n infrastructure
- `README_zh.md` Chinese documentation
- 82 pytest tests (59% coverage overall, agent core 76-100%)
- Python 3.10+ support

### Changed
- Architecture: standalone agent platform (removed skill/rule-engine dual-mode)
- CLI: function-based dispatch, agent mode is the default
- LLM temperature: centralized `DEFAULT_ANALYSIS_TEMPERATURE = 0.2` constant
- `.gitignore`: added secrets patterns, coverage artifacts, runtime files, knowledge base
- `setup.py`: Development Status `5 - Production/Stable`

### Usage
```bash
# Multi-agent review (default)
codespect-matrix

# CI gate
codespect-matrix --ci --json

# Code evolution analysis
codespect-matrix --evolve
codespect-matrix --evolve-baseline

# Self-evolution summary
codespect-matrix --evolve-self
```
