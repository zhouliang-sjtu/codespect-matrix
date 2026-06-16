"""codespect-matrix — 16-Agent Code Evolution Platform

Debate Review · Hybrid Engine · Code Evolution

The 16-agent QA team that doesn't just find bugs — it measures code health,
tracks technical debt, analyzes architecture, and generates improvement roadmaps.

Key Features:
- 16 specialized agents: Security, Healthcare, PHI, Architecture,
  Performance, DevOps, Testing, Linter, Data Science, Hardcode detection
- 5-phase review: Inspect → Cross-review → Debate → Converge → Fix
- Hybrid engine: Rule+LLM for security/healthcare; pure LLM for others
- Dual memory: Project-level + Global KB (cross-project learning)
- AI autonomous fix: Scan → fix plan → user confirm → execute
- Code evolution: Health scoring · Technical debt · Architecture analysis ·
  Test coverage · Improvement roadmap

Usage:
    # Default multi-agent review
    codespect-matrix

    # Code evolution analysis (health + debt + architecture)
    codespect-matrix --evolve

    # Full review with JSON output
    codespect-matrix --max-rounds 3 --json

    # AI autonomous fix
    codespect-matrix --fix-plan && codespect-matrix --fix-execute

    # Python API
    from codespect_matrix.agents import AgentOrchestrator
    orch = AgentOrchestrator(project_path="/my/project")
    orch.initialize()
    result = orch.run_full_cycle()
"""

__version__ = "1.0.0"
__author__ = "周良"
__organization__ = "上海交通大学医学院"

# Core
from .scanner import ProjectScanner
from .models import ProjectProfile
from .llm_service import LLMService, create_llm_service, get_llm_service
from .cli import main as cli_main

# Agent architecture
from .agents import (
    BaseAgent, AgentMessage, DebateResult, AgentRole,
    AgentCommunicationBus,
    ProjectMemory, GlobalKnowledgeBase,
    AgentOrchestrator,
)

# Evolution engine
from .evolution import (
    HealthScorer, TechDebtAnalyzer, ArchitectureAnalyzer,
    TestCoverageEstimator, EvolutionReporter, EvolutionBaseline,
    SelfEvolver,
)

__all__ = [
    # Core
    "ProjectScanner", "ProjectProfile",
    "LLMService", "create_llm_service", "get_llm_service",
    "cli_main",
    # Agent architecture
    "BaseAgent", "AgentMessage", "DebateResult", "AgentRole",
    "AgentCommunicationBus",
    "ProjectMemory", "GlobalKnowledgeBase",
    "AgentOrchestrator",
    # Evolution engine
    "HealthScorer", "TechDebtAnalyzer", "ArchitectureAnalyzer",
    "TestCoverageEstimator", "EvolutionReporter", "EvolutionBaseline",
    "SelfEvolver",
]
