"""Evolution engine — health scoring, technical debt, architecture analysis.

Core capabilities:
- Code Health Score: weighted finding severity → 0-100 normalized
- Technical Debt Index: TODO/FIXME/HACK density + complexity factors
- Architecture Health: import graph analysis, module coupling, God module detection
- Evolution Trend: baseline comparison, improvement/degradation tracking
"""

from __future__ import annotations

import os
import ast
import json
import hashlib
import subprocess
from datetime import datetime, UTC
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Set, Tuple


# ── Severity weight table ─────────────────────────────────────────────────────

SEVERITY_WEIGHTS = {
    "critical": 100,
    "high": 50,
    "medium": 15,
    "low": 3,
    "info": 0,
}


# ── Health Scoring ────────────────────────────────────────────────────────────

class HealthScorer:
    """Compute a 0-100 code health score from agent findings.

    Formula:
        raw_score = sum(severity_weight * count) per severity level
        max_score = sum(severity_weight * 10)  # 10 findings/severity as baseline
        health = max(0, 100 - (raw_score / max_score) * 100)

    Interpretation:
        90-100: Excellent — production-ready
        70-89:  Good — minor improvements needed
        50-69:  Fair — moderate technical debt
        30-49:  Poor — significant issues
        0-29:   Critical — requires immediate attention
    """

    def compute(self, findings: List[Dict]) -> Dict[str, Any]:
        """Compute health score from a list of finding dicts."""
        counts = Counter()
        for f in findings:
            sev = f.get("severity", "low")
            counts[sev] += 1

        raw_score = 0
        max_score = 0
        for sev, weight in SEVERITY_WEIGHTS.items():
            raw_score += weight * counts.get(sev, 0)
            max_score += weight * 10  # baseline: 10 findings per severity

        health = max(0.0, min(100.0, 100.0 - (raw_score / max(max_score, 1)) * 100.0))

        level = (
            "excellent" if health >= 90 else
            "good" if health >= 70 else
            "fair" if health >= 50 else
            "poor" if health >= 30 else
            "critical"
        )

        return {
            "health_score": round(health, 1),
            "level": level,
            "raw_penalty": raw_score,
            "severity_counts": dict(counts),
            "total_findings": len(findings),
        }


# ── Technical Debt ────────────────────────────────────────────────────────────

class TechDebtAnalyzer:
    """Analyze technical debt from code markers and complexity.

    Scans for:
    - TODO / FIXME / HACK / XXX / BUG markers
    - Comment-to-code ratio
    - Long files (>500 lines)
    - Deeply nested functions
    """

    MARKER_PATTERNS = ["TODO", "FIXME", "HACK", "XXX", "BUG", "WORKAROUND"]

    def analyze(self, project_path: str) -> Dict[str, Any]:
        """Scan project for technical debt indicators."""
        markers = []
        total_lines = 0
        total_comment_lines = 0
        file_stats = []

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build')]

            for file in files:
                if not file.endswith('.py'):
                    continue

                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, project_path)

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue

                file_lines = len(lines)
                total_lines += file_lines
                comment_lines = 0
                file_markers = []

                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        comment_lines += 1
                    for marker in self.MARKER_PATTERNS:
                        if marker in stripped and stripped.startswith('#'):
                            file_markers.append({
                                "marker": marker,
                                "line": i,
                                "content": stripped[:120],
                            })

                total_comment_lines += comment_lines

                if file_markers or file_lines > 500:
                    file_stats.append({
                        "file": relpath,
                        "lines": file_lines,
                        "comment_ratio": round(
                            comment_lines / max(file_lines, 1) * 100, 1,
                        ),
                        "markers": file_markers,
                        "overly_long": file_lines > 500,
                    })
                    markers.extend(file_markers)

        # Debt index calculation
        marker_penalty = len(markers) * 5
        large_file_penalty = sum(1 for f in file_stats if f["overly_long"]) * 10
        comment_penalty = max(
            0, 15 - round(total_comment_lines / max(total_lines, 1) * 100),
        ) * 2  # penalty if < 15% comments

        debt_index = min(100, marker_penalty + large_file_penalty + comment_penalty)
        level = "low" if debt_index < 20 else "moderate" if debt_index < 50 else "high" if debt_index < 80 else "critical"

        return {
            "debt_index": debt_index,
            "level": level,
            "marker_count": len(markers),
            "markers": markers,
            "large_files": [f for f in file_stats if f["overly_long"]],
            "file_details": file_stats[:30],
            "total_lines": total_lines,
            "comment_ratio": round(
                total_comment_lines / max(total_lines, 1) * 100, 1,
            ),
        }


# ── Architecture Analysis ─────────────────────────────────────────────────────

class ArchitectureAnalyzer:
    """Analyze project architecture: imports, coupling, module health.

    Builds a lightweight import graph and computes:
    - Fan-in / fan-out per module
    - Cyclic dependency detection (via DFS)
    - God module detection (>1000 lines + high fan-out)
    """

    def analyze(self, project_path: str) -> Dict[str, Any]:
        """Analyze architecture of a Python project."""
        imports = defaultdict(set)      # module → set of imported modules
        reverse_imports = defaultdict(set)  # module → set of modules that import it
        module_sizes = {}

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                       ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build')]

            for file in files:
                if not file.endswith('.py'):
                    continue

                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, project_path)
                module_name = relpath.replace(os.sep, '.').replace('.py', '')

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        source = f.read()
                    module_sizes[module_name] = len(source.splitlines())

                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports[module_name].add(alias.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imports[module_name].add(node.module.split('.')[0])
                except Exception:
                    continue

        # Build reverse map
        for mod, deps in imports.items():
            for dep in deps:
                reverse_imports[dep].add(mod)

        # Compute coupling
        coupling = {}
        for mod in imports:
            fan_out = len(imports[mod])
            fan_in = len(reverse_imports.get(mod, set()))
            coupling[mod] = {
                "fan_in": fan_in,
                "fan_out": fan_out,
                "coupling_score": min(100, (fan_in + fan_out) * 10),
                "lines": module_sizes.get(mod, 0),
            }

        # Detect cycles
        cycles = self._detect_cycles(imports)

        # God modules
        god_modules = [
            {
                "module": mod,
                "lines": coupling[mod]["lines"],
                "fan_out": coupling[mod]["fan_out"],
                "fan_in": coupling[mod]["fan_in"],
            }
            for mod, info in coupling.items()
            if info["lines"] > 1000 or info["fan_out"] > 15
        ]

        # Overall architecture health
        avg_coupling = (
            sum(c["coupling_score"] for c in coupling.values()) / max(len(coupling), 1)
        )
        health = max(0.0, 100.0 - avg_coupling - len(cycles) * 10)

        return {
            "architecture_health": round(health, 1),
            "level": self._health_level(health),
            "module_count": len(coupling),
            "avg_coupling_score": round(avg_coupling, 1),
            "god_modules": god_modules,
            "cycles": cycles,
            "top_coupled": sorted(
                coupling.items(),
                key=lambda x: x[1]["coupling_score"],
                reverse=True,
            )[:10],
        }

    def _detect_cycles(self, imports: Dict[str, Set[str]]) -> List[List[str]]:
        """Detect cycles in import graph via DFS."""
        cycles = []
        visited = set()
        stack = []

        def dfs(node, path):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for neighbor in imports.get(node, set()):
                dfs(neighbor, path[:])
            path.pop()

        # Only check project-internal modules
        project_modules = set(imports.keys())
        for mod in list(project_modules)[:50]:  # limit for performance
            dfs(mod, [])

        # Deduplicate: keep unique cycles
        unique = []
        seen = set()
        for cycle in cycles:
            key = tuple(sorted(cycle))
            if key not in seen:
                seen.add(key)
                unique.append(cycle)
        return unique

    @staticmethod
    def _health_level(score: float) -> str:
        if score >= 80:
            return "clean"
        if score >= 60:
            return "moderate"
        if score >= 40:
            return "tangled"
        return "critical"


# ── Test Coverage Estimator ──────────────────────────────────────────────────

class TestCoverageEstimator:
    """Estimate test coverage via pytest --cov when available."""

    def _count_test_files(self, project_path: str) -> int:
        """Count test files in project."""
        count = 0
        for root, dirs, files in os.walk(project_path):
            for file in files:
                if (file.startswith("test_") or file.endswith("_test.py")) and file.endswith(".py"):
                    count += 1
        return count

    def estimate(self, project_path: str) -> Dict:
        """Run pytest --cov and parse results."""
        # Try reading existing coverage.json first
        cov_path = os.path.join(project_path, "coverage.json")
        if os.path.exists(cov_path):
            try:
                with open(cov_path, 'r') as f:
                    data = json.load(f)
                totals = data.get("totals", {})
                pct = totals.get("percent_covered", 0)
                return {
                    "has_coverage": True,
                    "percent_covered": round(pct, 1),
                    "covered_lines": totals.get("covered_lines", 0),
                    "total_lines": totals.get("num_statements", 0),
                    "test_files_found": self._count_test_files(project_path),
                    "level": self._coverage_level(pct),
                }
            except Exception:
                pass

        # Try running pytest --cov
        try:
            result = subprocess.run(
                ["pytest", "--cov=" + project_path, "--cov-report=json",
                 "--cov-report=term", "-q"],
                cwd=project_path, capture_output=True, text=True, timeout=120,
            )
            if os.path.exists(cov_path):
                with open(cov_path, 'r') as f:
                    data = json.load(f)
                totals = data.get("totals", {})
                return {
                    "has_coverage": True,
                    "percent_covered": round(totals.get("percent_covered", 0), 1),
                    "covered_lines": totals.get("covered_lines", 0),
                    "total_lines": totals.get("num_statements", 0),
                    "test_files_found": self._count_test_files(project_path),
                    "level": self._coverage_level(totals.get("percent_covered", 0)),
                }
        except Exception:
            pass

        # Fallback: count test files
        return {
            "has_coverage": False,
            "percent_covered": 0,
            "test_files_found": self._count_test_files(project_path),
            "level": "unknown",
            "note": "Run `pip install pytest-cov` for accurate coverage",
        }

    @staticmethod
    def _coverage_level(pct: float) -> str:
        if pct >= 80:
            return "good"
        if pct >= 50:
            return "moderate"
        if pct > 0:
            return "low"
        return "none"


# ── Evolution Report Generator ────────────────────────────────────────────────

class EvolutionReporter:
    """Generate a comprehensive evolution report combining all analyses."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.health = HealthScorer()
        self.debt = TechDebtAnalyzer()
        self.arch = ArchitectureAnalyzer()
        self.coverage = TestCoverageEstimator()

    def full_report(
        self,
        agent_findings: List[Dict],
        baseline_data: Dict = None,
    ) -> Dict[str, Any]:
        """Generate a full evolution analysis report."""
        report = {
            "project": os.path.basename(self.project_path),
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "1.0.0",
        }

        # 1. Health Score
        report["health"] = self.health.compute(agent_findings)

        # 2. Technical Debt
        report["technical_debt"] = self.debt.analyze(self.project_path)

        # 3. Architecture
        report["architecture"] = self.arch.analyze(self.project_path)

        # 4. Test Coverage
        report["test_coverage"] = self.coverage.estimate(self.project_path)

        # 5. Overall score (weighted composite)
        health = report["health"]["health_score"]
        arch = report["architecture"]["architecture_health"]
        debt = 100 - report["technical_debt"]["debt_index"]
        cov = report["test_coverage"].get("percent_covered", 0)

        overall = round(health * 0.4 + arch * 0.25 + debt * 0.25 + cov * 0.1, 1)
        report["overall_score"] = overall
        report["overall_level"] = self._overall_level(overall)

        # 6. Baseline comparison
        if baseline_data:
            report["delta"] = self._compute_delta(report, baseline_data)

        # 7. Improvement roadmap
        report["roadmap"] = self._generate_roadmap(report)

        return report

    def _compute_delta(self, current: Dict, baseline: Dict) -> Dict:
        """Compute delta between current and baseline."""
        h_now = current["health"]["health_score"]
        h_before = baseline.get("health", {}).get("health_score", h_now)
        d_now = current["technical_debt"]["debt_index"]
        d_before = baseline.get("technical_debt", {}).get("debt_index", d_now)
        findings_now = current["health"]["total_findings"]
        findings_before = baseline.get("health", {}).get("total_findings", findings_now)

        trend = (
            "improving" if h_now > h_before and d_now < d_before else
            "degrading" if h_now < h_before and d_now > d_before else
            "stable"
        )

        return {
            "trend": trend,
            "health_delta": round(h_now - h_before, 1),
            "debt_delta": round(d_now - d_before, 1),
            "findings_delta": findings_now - findings_before,
        }

    def _overall_level(self, score: float) -> str:
        if score >= 85:
            return "excellent"
        if score >= 70:
            return "good"
        if score >= 50:
            return "fair"
        if score >= 30:
            return "needs_work"
        return "critical"

    def _generate_roadmap(self, report: Dict) -> List[Dict]:
        """Generate prioritized improvement roadmap."""
        items = []

        h = report["health"]
        d = report["technical_debt"]
        a = report["architecture"]
        c = report["test_coverage"]

        if h["health_score"] < 70:
            items.append({
                "priority": "P0",
                "category": "quality",
                "action": "Fix critical and high-severity findings",
                "rationale": f"Health score {h['health_score']} — {h['severity_counts']}",
                "effort": "varies",
            })

        if d["debt_index"] > 30 and d["marker_count"] > 0:
            items.append({
                "priority": "P1",
                "category": "technical_debt",
                "action": f"Resolve {d['marker_count']} TODO/FIXME/HACK markers",
                "rationale": f"Debt index {d['debt_index']}/100",
                "effort": f"{d['marker_count'] * 0.5:.0f}h estimated",
            })

        if d["debt_index"] > 30 and len(d.get("large_files", [])) > 0:
            large = [f["file"] for f in d["large_files"][:3]]
            items.append({
                "priority": "P2",
                "category": "technical_debt",
                "action": f"Split {len(d['large_files'])} oversized files (>500 lines)",
                "rationale": f"Large files: {', '.join(large)}",
                "effort": f"{len(d['large_files']) * 2}h estimated",
            })

        if a["god_modules"]:
            items.append({
                "priority": "P1",
                "category": "architecture",
                "action": f"Refactor {len(a['god_modules'])} God modules",
                "rationale": ", ".join(m["module"] for m in a["god_modules"][:3]),
                "effort": "2-4h per module",
            })

        if a["cycles"]:
            items.append({
                "priority": "P2",
                "category": "architecture",
                "action": f"Break {len(a['cycles'])} import cycles",
                "rationale": "Cyclic dependencies hurt maintainability",
                "effort": "1-2h per cycle",
            })

        if c.get("percent_covered", 0) < 50:
            items.append({
                "priority": "P2",
                "category": "testing",
                "action": "Increase test coverage to 50%+",
                "rationale": f"Current coverage: {c.get('percent_covered', 0)}%",
                "effort": "depends on project size",
            })

        return items


# ── Baseline persistence ──────────────────────────────────────────────────────

class EvolutionBaseline:
    """Save and load evolution baselines for trend tracking."""

    BASELINE_FILE = ".codespect_matrix_evolution_baseline.json"

    def __init__(self, project_path: str):
        self.path = os.path.join(project_path, self.BASELINE_FILE)

    def save(self, report: Dict):
        """Save current evolution report as baseline."""
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    def load(self) -> Optional[Dict]:
        """Load a previous baseline."""
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def diff(self, current: Dict) -> Optional[Dict]:
        """Compare current report against baseline."""
        previous = self.load()
        if not previous:
            return None

        h_now = current["health"]["health_score"]
        h_before = previous.get("health", {}).get("health_score", h_now)
        d_now = current["technical_debt"]["debt_index"]
        d_before = previous.get("technical_debt", {}).get("debt_index", d_now)

        trend = (
            "improving" if h_now > h_before and d_now < d_before else
            "degrading" if h_now < h_before and d_now > d_before else
            "stable"
        )

        delta_summary = {
            "trend": trend,
            "health_now": round(h_now, 1),
            "health_before": round(h_before, 1),
            "health_delta": round(h_now - h_before, 1),
            "debt_now": d_now,
            "debt_before": d_before,
            "debt_delta": d_now - d_before,
        }

        # Compare finding counts
        if "health" in previous and "health" in current:
            prev_findings = previous["health"].get("total_findings", 0)
            curr_findings = current["health"].get("total_findings", 0)
            delta_summary["findings_delta"] = curr_findings - prev_findings

        return delta_summary


# ════════════════════════════════════════════════════════════════════════
# Self-Evolution Engine — learns from QA → Fix → Re-QA cycles
# ════════════════════════════════════════════════════════════════════════

SELF_EVOLVE_PATH = os.path.join(os.path.expanduser("~"), ".codespect_matrix_knowledge", "self_evolution.json")


class SelfEvolver:
    """Learns from QA cycles across projects to improve future scans.

    Tracks the full loop:
    1. Scan → findings
    2. Fix → apply remediation
    3. Re-scan → verify health delta
    4. Learn → update pattern confidence, agent weights, fix templates

    Over time, the tool becomes more accurate because it knows:
    - Which patterns produce real vs false-positive findings
    - Which fix templates actually work
    - Which agents are most effective for each project type
    """

    def __init__(self):
        os.makedirs(os.path.dirname(SELF_EVOLVE_PATH), exist_ok=True)
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(SELF_EVOLVE_PATH):
            try:
                with open(SELF_EVOLVE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "version": "1.0.0",
            "created": datetime.now(UTC).isoformat(),
            "qa_cycles": [],           # Full QA cycle records
            "fix_effectiveness": {},   # check_name → success/fail counts
            "agent_performance": {},   # agent → accuracy stats
            "learned_patterns": {},    # patterns discovered from fixes
            "evolution_generations": 0,
            "total_cycles": 0,
            "total_projects": set(),   # dedup via list on save
        }

    def _save(self):
        # Convert set to list for JSON serialization
        self.data["total_projects"] = list(self.data["total_projects"])
        with open(SELF_EVOLVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False, default=str)

    # ─── Cycle Recording ─────────────────────────────────────────────────

    def record_qa_cycle(self, project_name: str,
                        before_health: float,
                        findings: List[Dict],
                        fixes_applied: List[Dict],
                        after_health: Optional[float] = None,
                        fix_details: Optional[List[Dict]] = None):
        """Record a complete QA → Fix → Re-QA cycle.

        Args:
            project_name: project identifier
            before_health: health score before fixing
            findings: list of {check_name, severity, message, agent}
            fixes_applied: list of {check_name, fix_type, success, description}
            after_health: health score after fixing (None if not re-scanned)
            fix_details: detailed fix reasoning {check_name, reasoning, old_code, new_code}
        """
        cycle = {
            "project": project_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "before_health": before_health,
            "after_health": after_health,
            "health_delta": round(after_health - before_health, 1) if after_health else None,
            "findings_count": len(findings),
            "findings": findings,
            "fixes_applied": fixes_applied,
            "fix_details": fix_details or [],
            "generation": self.data["evolution_generations"],
        }
        self.data["qa_cycles"].append(cycle)
        self.data["total_cycles"] += 1
        self.data["total_projects"].add(project_name)

        # Track fix effectiveness
        for fix in fixes_applied:
            check = fix.get("check_name", "unknown")
            success = fix.get("success", False)
            if check not in self.data["fix_effectiveness"]:
                self.data["fix_effectiveness"][check] = {"success": 0, "fail": 0}
            if success:
                self.data["fix_effectiveness"][check]["success"] += 1
            else:
                self.data["fix_effectiveness"][check]["fail"] += 1

        # Track agent performance
        for finding in findings:
            agent = finding.get("agent", "unknown")
            severity = finding.get("severity", "low")
            if agent not in self.data["agent_performance"]:
                self.data["agent_performance"][agent] = {
                    "findings": 0, "useful": 0, "false_positive": 0,
                    "severity_weights": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                }
            self.data["agent_performance"][agent]["findings"] += 1
            self.data["agent_performance"][agent]["severity_weights"][severity] += 1

        # Learn from fix details
        if fix_details:
            self._learn_from_fixes(fix_details, findings)

        self._save()

    def _learn_from_fixes(self, fix_details: List[Dict], findings: List[Dict]):
        """Extract patterns from successful fixes.

        When a fix works (health improves), capture:
        - The pattern that triggered the finding
        - The reasoning behind the fix
        - The actual code change
        """
        findings_map = {f.get("check_name"): f for f in findings}
        for fix in fix_details:
            check = fix.get("check_name", "")
            reasoning = fix.get("reasoning", "")
            if not check or not reasoning:
                continue

            if check not in self.data["learned_patterns"]:
                self.data["learned_patterns"][check] = {
                    "discovered_at": datetime.now(UTC).isoformat(),
                    "occurrences": 0,
                    "reasonings": [],
                    "successful_templates": [],
                }
            entry = self.data["learned_patterns"][check]
            entry["occurrences"] += 1
            if reasoning not in entry["reasonings"]:
                entry["reasonings"].append(reasoning)
            if fix.get("new_code"):
                entry["successful_templates"].append({
                    "old_code": fix.get("old_code", "")[:200],
                    "new_code": fix["new_code"][:200],
                    "reasoning": reasoning[:300],
                })

    # ─── Intelligence Queries ────────────────────────────────────────────

    def get_fix_confidence(self, check_name: str) -> float:
        """How likely a fix for this check will succeed (0.0-1.0)."""
        stats = self.data["fix_effectiveness"].get(check_name)
        if not stats:
            return 0.5  # unknown — neutral
        total = stats["success"] + stats["fail"]
        if total == 0:
            return 0.5
        return stats["success"] / total

    def get_best_agents(self, project_type: str = None, top_n: int = 8) -> List[str]:
        """Return most effective agents, optionally filtered by project type."""
        perf = self.data["agent_performance"]
        if not perf:
            return []

        scored = []
        for agent, stats in perf.items():
            if stats["findings"] == 0:
                continue
            # Score: how many useful findings per total, weighted by severity mix
            useful_ratio = (stats.get("useful", 0) + 1) / (stats["findings"] + 1)
            sev = stats["severity_weights"]
            sev_score = sev.get("critical", 0) * 10 + sev.get("high", 0) * 4 + sev.get("medium", 0)
            total_score = useful_ratio * (sev_score + 1)
            scored.append((agent, total_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [a[0] for a in scored[:top_n]]

    def get_known_fix(self, check_name: str) -> Optional[str]:
        """Return a previously successful fix reasoning for a check."""
        patterns = self.data["learned_patterns"].get(check_name)
        if patterns and patterns.get("reasonings"):
            return patterns["reasonings"][0]
        return None

    def get_evolution_summary(self) -> Dict:
        """Summary of how much the tool has learned."""
        cycles = self.data["qa_cycles"]
        if not cycles:
            return {"status": "no_data", "message": "No QA cycles recorded yet"}

        health_deltas = [c["health_delta"] for c in cycles if c.get("health_delta") is not None]
        avg_delta = sum(health_deltas) / len(health_deltas) if health_deltas else 0

        return {
            "generation": self.data["evolution_generations"],
            "total_cycles": self.data["total_cycles"],
            "projects_helped": len(self.data["total_projects"]),
            "average_health_improvement": round(avg_delta, 1),
            "fix_effectiveness": {
                check: {
                    "confidence": round(s["success"] / max(s["success"] + s["fail"], 1), 2),
                    "total": s["success"] + s["fail"],
                }
                for check, s in sorted(
                    self.data["fix_effectiveness"].items(),
                    key=lambda x: x[1]["success"] + x[1]["fail"],
                    reverse=True,
                )[:10]
            },
            "top_agents": self.get_best_agents(top_n=5),
            "patterns_learned": len(self.data["learned_patterns"]),
            "knowledge_base_path": SELF_EVOLVE_PATH,
        }

    def evolve(self) -> Dict:
        """Advance one evolution generation.

        Aggregates learnings from all cycles, updates pattern confidence,
        prunes low-confidence patterns, adjusts agent weights.

        Returns generation summary.
        """
        self.data["evolution_generations"] += 1
        gen = self.data["evolution_generations"]

        # Prune fix templates with <30% success rate and <3 attempts
        to_prune = []
        for check, stats in self.data["fix_effectiveness"].items():
            total = stats["success"] + stats["fail"]
            if total >= 3 and stats["success"] / total < 0.3:
                to_prune.append(check)
        for check in to_prune:
            del self.data["fix_effectiveness"][check]
            if check in self.data["learned_patterns"]:
                del self.data["learned_patterns"][check]

        # Promote successful learned patterns to cross-project knowledge base
        try:
            from .agents.memory import GlobalKnowledgeBase
            kb = GlobalKnowledgeBase()
            for check, entry in self.data["learned_patterns"].items():
                if entry["occurrences"] >= 2 and entry.get("reasonings"):
                    kb.learn_pattern(
                        check_name=check,
                        category="self_evolved",
                        pattern=entry["reasonings"][0][:100],
                        fix_template=entry["reasonings"][0],
                        severity="medium",
                    )
        except Exception:
            pass  # GlobalKnowledgeBase not available in all contexts

        self._save()
        return {
            "generation": gen,
            "patterns_promoted": len(self.data["learned_patterns"]),
            "pruned_templates": len(to_prune),
            "cycles_learned": self.data["total_cycles"],
        }

    def _finalize(self):
        """Convert set back for JSON."""
        self.data["total_projects"] = list(self.data["total_projects"])
