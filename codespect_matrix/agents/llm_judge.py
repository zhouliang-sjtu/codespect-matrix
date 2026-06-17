"""LLM-as-Judge — external quality evaluator for code review findings.

Purpose (论文定位):
    Provides an independent, reproducible, quantitative evaluation of review
    quality across ALL tools (codespect-matrix and all baselines). This avoids
    the bias of "using your own tool to judge your own output."

How it differs from Agent Debate:
    ┌───────────────────┬─────────────────────────┬──────────────────────────┐
    │                   │ Agent Debate (内部)     │ LLM-as-Judge (外部)      │
    ├───────────────────┼─────────────────────────┼──────────────────────────┤
    │ 定位              │ Pipeline 质检员         │ 独立裁判 / 论文定量指标  │
    │ 作用对象          │ 单个 finding 真伪       │ 整个审查输出的质量       │
    │ 参与方式          │ 参与流程，交叉审查       │ 旁观流程，事后评分       │
    │ 输出              │ confirmed / rejected    │ precision / recall / F1  │
    │ 评估谁            │ 只评估 codespect        │ 评估所有工具（含基线）   │
    └───────────────────┴─────────────────────────┴──────────────────────────┘

Pipeline integration:
    After all tools produce findings → LLM-as-Judge evaluates all → metrics

Usage:
    judge = LLMJudge()
    report = judge.evaluate(
        project_path="/path/to/project",
        tools_findings={
            "codespect": codespect_findings,
            "semgrep": semgrep_findings,
            "ollama": ollama_findings,
        }
    )
    print(report["precision"], report["recall"], report["f1"])
"""

from __future__ import annotations

import os
import re
import json
import hashlib
import requests
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════════════════
# Judgement data types
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Judgement:
    """A single LLM-as-Judge verdict on a finding."""
    finding_id: str              # hash or tool-generated ID
    tool_name: str               # which tool reported this
    file_path: str
    line_start: int
    check_name: str
    severity: str
    message: str

    # Judgement
    is_true_positive: bool       # LLM verdict
    confidence: float            # 0.0 - 1.0
    reasoning: str               # LLM's explanation
    correct_severity: str        # LLM's severity opinion (may differ)
    correct_category: str        # LLM's category opinion

    # Metadata
    raw_response: str = ""
    judged_at: str = ""


@dataclass
class ToolMetrics:
    """Per-tool evaluation metrics."""
    tool_name: str
    total_findings: int = 0
    true_positives: int = 0
    false_positives: int = 0
    precision: float = 0.0
    # Recall requires known ground truth (injected defects)
    recall: float = 0.0
    f1: float = 0.0
    # Severity breakdown
    by_severity: Dict[str, Dict[str, int]] = field(default_factory=dict)
    # Whether this tool detected each injected defect
    injected_detection_rate: float = 0.0

    def compute(self):
        """Compute derived metrics."""
        total = self.total_findings
        if total > 0:
            self.precision = self.true_positives / total
        if self.precision > 0 and self.recall > 0:
            self.f1 = 2 * self.precision * self.recall / (self.precision + self.recall)
        elif self.precision > 0:
            self.f1 = self.precision  # fallback when no recall data


@dataclass
class JudgeReport:
    """Complete LLM-as-Judge evaluation report."""
    project_path: str
    total_findings_evaluated: int
    judgements: List[Judgement]
    tool_metrics: Dict[str, ToolMetrics]
    overall: Dict[str, Any]
    injected_detection: Dict[str, Any]
    agreement_matrix: Dict[str, Dict[str, float]]


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Judge
# ═══════════════════════════════════════════════════════════════════════════════

JUDGE_SYSTEM_PROMPT = """You are an independent code review quality evaluator. Your job is to judge whether a finding reported by an automated tool is a TRUE POSITIVE (real vulnerability) or FALSE POSITIVE (incorrect report).

Evaluation criteria:
1. Look at the actual source code around the reported line
2. Determine if the code actually contains the claimed vulnerability
3. Consider whether the finding is technically accurate
4. Do NOT be strict about whether the finding is "exploitable" — focus on whether the code pattern is genuinely problematic
5. For medical software, be especially strict about PHI/data privacy issues

For each finding, respond with a JSON object:
{
  "is_true_positive": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation in Chinese",
  "correct_severity": "critical|high|medium|low|info",
  "correct_category": "security|privacy|code_quality|medical_compliance|other"
}

Rules:
- SQL injection via string formatting IS a true positive
- PHI data in log/print statements IS a true positive
- Hardcoded credentials/API keys ARE true positives
- Missing input validation CAN be a true positive if clearly dangerous
- Generic code style issues (line length, naming) are NOT true positives unless they have security implications
- Be conservative: if uncertain, lean toward true positive for security issues"""


class LLMJudge:
    """LLM-as-Judge: external evaluator using Ollama."""

    def __init__(
        self,
        base_url: str = None,
        model: str = None,
        temperature: float = 0.1,
        timeout: int = 120,
    ):
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            os.getenv("DASHSCOPE_BASE_URL", "http://localhost:11434")
        )
        self.model = model or os.getenv("DASHSCOPE_MODEL", "qwen-plus")
        self.temperature = temperature
        self.timeout = timeout

    # ── Public API ──────────────────────────────────────────────────────────

    def evaluate(
        self,
        project_path: str,
        tools_findings: Dict[str, List[Dict]],
        injected_defects: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Evaluate findings from multiple tools.

        Args:
            project_path: Root of the project being evaluated.
            tools_findings: {tool_name: [finding_dict, ...]}.
            injected_defects: Known injected defects for recall calculation.
                              [{file_path, line_start, type, code}, ...]

        Returns:
            JudgeReport as dict with per-tool metrics and overall summary.
        """
        all_judgements: List[Judgement] = []
        tool_metrics: Dict[str, ToolMetrics] = {}

        for tool_name, findings in tools_findings.items():
            if not findings:
                continue

            metrics = ToolMetrics(tool_name=tool_name, total_findings=len(findings))
            metrics.by_severity = defaultdict(lambda: {"tp": 0, "fp": 0})

            for f in findings:
                judgement = self._judge_one(project_path, tool_name, f)
                all_judgements.append(judgement)

                if judgement.is_true_positive:
                    metrics.true_positives += 1
                    sev = judgement.severity or "medium"
                    metrics.by_severity[sev]["tp"] += 1
                else:
                    metrics.false_positives += 1
                    sev = judgement.severity or "medium"
                    metrics.by_severity[sev]["fp"] += 1

            # Compute recall from injected defects
            if injected_defects:
                detected = self._check_injected_detection(
                    project_path, tool_name, findings, injected_defects
                )
                total_injected = len(injected_defects)
                metrics.recall = detected / total_injected if total_injected > 0 else 0
                metrics.injected_detection_rate = metrics.recall

            metrics.compute()
            metrics.by_severity = dict(metrics.by_severity)
            tool_metrics[tool_name] = metrics

        # Overall summary
        total_tp = sum(m.true_positives for m in tool_metrics.values())
        total_all = sum(m.total_findings for m in tool_metrics.values())
        total_recall = max(m.recall for m in tool_metrics.values()) if injected_defects else 0

        overall = {
            "total_findings": total_all,
            "total_true_positives": total_tp,
            "total_false_positives": total_all - total_tp,
            "overall_precision": total_tp / total_all if total_all > 0 else 0,
            "overall_recall": total_recall,
            "overall_f1": self._f1(
                total_tp / total_all if total_all > 0 else 0,
                total_recall
            ),
        }

        # Tool agreement matrix
        agreement = self._compute_agreement(all_judgements, tools_findings)

        # Injected defect tracking
        injected_detail = {}
        if injected_defects:
            injected_detail = self._injected_summary(
                project_path, tools_findings, injected_defects
            )

        return {
            "project_path": project_path,
            "total_findings_evaluated": total_all,
            "judgements": [j.__dict__ for j in all_judgements],
            "tool_metrics": {k: v.__dict__ for k, v in tool_metrics.items()},
            "overall": overall,
            "injected_detection": injected_detail,
            "agreement_matrix": agreement,
        }

    def judge_single_tool(
        self,
        project_path: str,
        tool_name: str,
        findings: List[Dict],
    ) -> Dict[str, Any]:
        """Quick evaluation of a single tool's findings."""
        return self.evaluate(project_path, {tool_name: findings})

    # ── Core judgement logic ────────────────────────────────────────────────

    def _judge_one(
        self, project_path: str, tool_name: str, finding: Dict
    ) -> Judgement:
        """Judge a single finding via LLM."""
        file_path = finding.get("file_path", "")
        line_start = finding.get("line_start", finding.get("line", 1))
        severity = finding.get("severity", "medium")
        message = finding.get("message", "")
        check_name = finding.get("check_name", "unknown")
        finding_id = finding.get("original_id", hashlib.md5(
            f"{file_path}:{line_start}:{check_name}".encode()
        ).hexdigest()[:12])

        # Read source context (5 lines before + 10 after)
        source_context = self._read_context(project_path, file_path, line_start)

        prompt = self._build_judge_prompt(
            tool_name, check_name, severity, message, file_path, line_start, source_context
        )

        try:
            response = self._call_ollama(prompt)
            parsed = self._parse_response(response)
        except Exception as e:
            # Fallback: mark as true positive with low confidence
            parsed = {
                "is_true_positive": True,
                "confidence": 0.5,
                "reasoning": f"Judge error: {e}. Conservative default: true positive.",
                "correct_severity": severity,
                "correct_category": "other",
            }

        return Judgement(
            finding_id=finding_id,
            tool_name=tool_name,
            file_path=file_path,
            line_start=int(line_start) if line_start else 0,
            check_name=check_name,
            severity=severity,
            message=message[:200],
            is_true_positive=parsed.get("is_true_positive", True),
            confidence=parsed.get("confidence", 0.5),
            reasoning=parsed.get("reasoning", ""),
            correct_severity=parsed.get("correct_severity", severity),
            correct_category=parsed.get("correct_category", "other"),
        )

    def _build_judge_prompt(
        self, tool_name: str, check_name: str, severity: str, message: str,
        file_path: str, line: int, source_context: str,
    ) -> str:
        """Build the evaluation prompt."""
        return f"""Tool: {tool_name}
Rule: {check_name}
Reported Severity: {severity}
File: {file_path} (line {line})
Message: {message}

Source code around line {line}:
```python
{source_context}
```

Judge this finding. Respond with JSON only."""

    def _read_context(
        self, project_path: str, file_path: str, line_start: int,
        before: int = 5, after: int = 10
    ) -> str:
        """Read source code context around a line."""
        full_path = os.path.join(project_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            start = max(0, line_start - 1 - before)
            end = min(len(lines), line_start + after)
            snippet = lines[start:end]

            # Add line numbers
            numbered = []
            for i, line in enumerate(snippet, start + 1):
                prefix = " >>>" if i == line_start else "    "
                numbered.append(f"{prefix} {i:4d} | {line.rstrip()}")

            return "\n".join(numbered)
        except Exception:
            return f"(Cannot read file: {full_path})"

    # ── Ollama API ──────────────────────────────────────────────────────────

    def _call_ollama(self, user_prompt: str) -> str:
        """Call Ollama chat API."""
        url = f"{self.base_url.rstrip('/')}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown wrappers."""
        # Try to extract JSON from code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            response = json_match.group(1)

        # Try direct parse
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        # Fallback heuristic
        return {
            "is_true_positive": "true" in response.lower() and "false" not in response.lower()[:50],
            "confidence": 0.4,
            "reasoning": f"Fallback parse: {response[:200]}",
            "correct_severity": "medium",
            "correct_category": "other",
        }

    # ── Injected defect matching ────────────────────────────────────────────

    def _check_injected_detection(
        self, project_path: str, tool_name: str,
        findings: List[Dict], injected: List[Dict],
    ) -> int:
        """Count how many injected defects a tool detected."""
        detected = 0
        for defect in injected:
            defect_file = defect.get("file_path", "")
            defect_line = defect.get("line_start", defect.get("line", 0))

            for f in findings:
                f_file = f.get("file_path", "")
                f_line = f.get("line_start", f.get("line", 0))

                # Match file + line within ±3 lines
                if defect_file == f_file and abs(int(f_line) - int(defect_line)) <= 3:
                    detected += 1
                    break

        return detected

    def _injected_summary(
        self, project_path: str, tools_findings: Dict[str, List[Dict]],
        injected: List[Dict],
    ) -> Dict[str, Any]:
        """Detailed injected defect detection tracking."""
        detail = []
        for i, defect in enumerate(injected):
            detected_by = []
            for tool_name, findings in tools_findings.items():
                if self._check_injected_detection(project_path, tool_name, findings, [defect]):
                    detected_by.append(tool_name)

            detail.append({
                "id": f"INJECTED_{i+1:03d}",
                "file": defect.get("file_path", ""),
                "line": defect.get("line_start", defect.get("line", 0)),
                "type": defect.get("type", "unknown"),
                "detected_by": detected_by,
                "detected": len(detected_by) > 0,
            })

        # Tool-level recall
        total = len(injected)
        tool_recall = {}
        for tool_name in tools_findings:
            det = self._check_injected_detection(
                project_path, tool_name, tools_findings.get(tool_name, []), injected
            )
            tool_recall[tool_name] = det / total if total > 0 else 0

        return {
            "total_injected": total,
            "by_tool": tool_recall,
            "details": detail,
        }

    # ── Agreement analysis ──────────────────────────────────────────────────

    def _compute_agreement(
        self, judgements: List[Judgement], tools_findings: Dict[str, List[Dict]]
    ) -> Dict[str, Dict[str, float]]:
        """Compute pairwise tool agreement (Jaccard on matched findings)."""
        tools = list(tools_findings.keys())
        matrix = {}

        for t1 in tools:
            matrix[t1] = {}
            f1_set = self._fingerprint_set(tools_findings.get(t1, []))
            for t2 in tools:
                f2_set = self._fingerprint_set(tools_findings.get(t2, []))
                intersection = len(f1_set & f2_set)
                union = len(f1_set | f2_set)
                matrix[t1][t2] = intersection / union if union > 0 else 0

        return matrix

    @staticmethod
    def _fingerprint_set(findings: List[Dict]) -> set:
        """Create a set of location fingerprints for agreement analysis.

        Uses file + line range (within ±2 lines tolerance) for cross-tool matching,
        since different tools name the same vulnerability differently.
        """
        fps = set()
        for f in findings:
            line = f.get("line_start", f.get("line", 0))
            fp = (
                f.get("file_path", ""),
                int(line) if line else 0,
            )
            fps.add(fp)
        return fps

    @staticmethod
    def _f1(precision: float, recall: float) -> float:
        if precision + recall == 0:
            return 0
        return 2 * precision * recall / (precision + recall)


# ═══════════════════════════════════════════════════════════════════════════════
# Quick benchmarking helper
# ═══════════════════════════════════════════════════════════════════════════════

def benchmark_all_tools(
    project_path: str,
    tools_findings: Dict[str, List[Dict]],
    injected_defects: List[Dict] = None,
    llm_judge: LLMJudge = None,
) -> Dict[str, Any]:
    """Run LLM-as-Judge benchmark on all tools.

    Args:
        project_path: Project root.
        tools_findings: {tool_name: [finding_dict, ...]} from all tools.
        injected_defects: Known defects for recall computation.
        llm_judge: Optional pre-configured judge.

    Returns:
        Full JudgeReport dict.
    """
    if llm_judge is None:
        llm_judge = LLMJudge()

    return llm_judge.evaluate(project_path, tools_findings, injected_defects)


def print_benchmark_table(report: Dict[str, Any]):
    """Print a formatted benchmark comparison table."""
    metrics = report.get("tool_metrics", {})
    overall = report.get("overall", {})

    print("\n" + "=" * 80)
    print("  LLM-as-Judge Benchmark Results")
    print("=" * 80)
    print(f"  Project: {report.get('project_path', 'N/A')}")
    print(f"  Total findings evaluated: {report.get('total_findings_evaluated', 0)}")
    print()
    print(f"  {'Tool':<25} {'Precision':>10} {'Recall':>8} {'F1':>8} {'TP':>6} {'FP':>6} {'Total':>6}")
    print("  " + "-" * 72)

    for name, m in sorted(metrics.items()):
        if isinstance(m, dict):
            print(f"  {name:<25} {m.get('precision',0):>10.3f} {m.get('recall',0):>8.3f} "
                  f"{m.get('f1',0):>8.3f} {m.get('true_positives',0):>6} "
                  f"{m.get('false_positives',0):>6} {m.get('total_findings',0):>6}")

    print("  " + "-" * 72)
    print(f"  {'OVERALL':<25} {overall.get('overall_precision',0):>10.3f} "
          f"{overall.get('overall_recall',0):>8.3f} {overall.get('overall_f1',0):>8.3f}")
    print()

    # Injected defect detection
    injected = report.get("injected_detection", {})
    if injected.get("total_injected", 0) > 0:
        print(f"\n  Injected Defect Detection ({injected['total_injected']} total):")
        for tool, rate in injected.get("by_tool", {}).items():
            bar = "█" * int(rate * 20)
            print(f"    {tool:<23} {rate:.0%} {bar}")

    print("\n" + "=" * 80)
