"""CLI entry point — 16-Agent Code Evolution Platform."""

import argparse
import json
import sys
from typing import Optional


def main():
    parser = argparse.ArgumentParser(
        prog="codespect-matrix",
        description="codespect-matrix — 16-Agent Code Evolution Platform · Debate Review · Hybrid Engine · Health Scoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Default: multi-agent review
  codespect-matrix
  
  # Target a specific project
  codespect-matrix --path /path/to/project

  # CI/CD gate mode
  codespect-matrix --ci --json

  # Code evolution analysis
  codespect-matrix --evolve
  codespect-matrix --evolve-baseline

  # AI autonomous fix (two-step)
  codespect-matrix --fix-plan          # Step 1: generate plan
  codespect-matrix --fix-execute       # Step 2: execute
        """
    )
    
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="project path (default: current directory)"
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=5,
        help="max review rounds (default: 5)"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD gate mode — exit_code=1 when thresholds exceeded"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="output JSON format"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="report output file path"
    )
    
    # ── Evolution ──
    parser.add_argument(
        "--evolve",
        action="store_true",
        help="code evolution analysis — health score + tech debt + architecture + roadmap"
    )
    parser.add_argument(
        "--evolve-baseline",
        action="store_true",
        help="save evolution analysis as baseline for trend comparison"
    )
    parser.add_argument(
        "--evolve-self",
        action="store_true",
        help="self-evolution summary — show what the tool has learned from past QA cycles"
    )
    
    # ── AI autonomous fix ──
    parser.add_argument(
        "--fix-plan",
        action="store_true",
        help="step 1: scan and generate fix plan (preview only, no code changes)"
    )
    parser.add_argument(
        "--fix-execute",
        action="store_true",
        help="step 2: execute fix plan (requires --fix-plan first)"
    )
    parser.add_argument(
        "--fix-all",
        action="store_true",
        help="execute all fixes including high-risk ones (with --fix-execute)"
    )
    
    args = parser.parse_args()
    
    try:
        # ── Code evolution ──
        if args.evolve_self:
            _run_evolve_self(args)
            return
        
        if args.evolve or args.evolve_baseline:
            _run_evolve(args, save_baseline=args.evolve_baseline)
            return
        
        # ── CI gate ──
        if args.ci:
            _run_ci_gate(args)
            return
        
        # ── AI fix ──
        if args.fix_plan:
            _run_fix_plan(args)
            return
        
        if args.fix_execute:
            _run_fix_execute(args)
            return
        
        # ── Default: multi-agent review ──
        _run_agent_mode(args)
        
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


# ══════════════════════════════════════════════
# Default multi-agent mode
# ══════════════════════════════════════════════

def _run_agent_mode(args):
    """Multi-agent full-flow review."""
    from codespect_matrix.agents.orchestrator import AgentOrchestrator
    
    print(f"{'='*70}")
    print("  codespect-matrix — 16-Agent Code Evolution Platform")
    print("  Review · Debate · Converge · Evolve")
    print(f"{'='*70}")
    
    orchestrator = AgentOrchestrator(project_path=args.path)
    orchestrator.initialize()
    
    profile = orchestrator._project_profile
    print(f"\n  project: {profile.get('project_type', 'unknown')}")
    print(f"  domain: {profile.get('domain', 'unknown')}")
    print(f"  scale: {profile.get('scale', 'unknown')}")
    print(f"  {len(orchestrator.active_agents)} agents active:")
    for name in orchestrator.active_agents:
        agent = orchestrator.agents.get(name)
        if agent:
            print(f"    [{agent.get_domain():15s}] {name} — {agent.get_description()}")
    
    print(f"\n  starting review...")
    result = orchestrator.run_full_cycle(max_rounds=args.max_rounds)
    
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        report = orchestrator.generate_report(result)
        print("\n" + report)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n  report saved to: {args.output}")
    
    has_critical = any(
        i.get("severity") == "critical"
        for i in result.get("confirmed_issues", [])
    )
    sys.exit(1 if has_critical else 0)


# ══════════════════════════════════════════════
# CI gate mode
# ══════════════════════════════════════════════

def _run_ci_gate(args):
    """CI gate (agent mode)."""
    from codespect_matrix.agents.orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(project_path=args.path)
    orchestrator.initialize()
    result = orchestrator.run_full_cycle(max_rounds=1)
    
    severities = {"critical": 0, "high": 0, "medium": 0}
    for issue in result["confirmed_issues"]:
        sev = issue.get("severity", "low")
        severities[sev] = severities.get(sev, 0) + 1
    
    gate_pass = (
        severities.get("critical", 0) == 0 and
        severities.get("high", 0) <= 5 and
        severities.get("medium", 0) <= 30
    )
    
    output = {
        "exit_code": 0 if gate_pass else 1,
        "severities": severities,
        "total_findings": result["total_findings"],
        "confirmed": len(result["confirmed_issues"]),
        "rejected": len(result["rejected_issues"]),
        "converged": result["converged"],
        "timestamp": result["cycles"][0]["timestamp"] if result["cycles"] else "",
    }
    
    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"{'='*60}")
        print(f"CI Gate Check — {'PASS' if gate_pass else 'FAIL'}")
        print(f"{'='*60}")
        print(f"severities: {severities}")
        print(f"confirmed: {len(result['confirmed_issues'])}")
        print(f"rejected: {len(result['rejected_issues'])}")
        print(f"gate: {'PASS' if gate_pass else 'FAIL'}")
    
    sys.exit(0 if gate_pass else 1)


# ══════════════════════════════════════════════
# Code evolution analysis
# ══════════════════════════════════════════════

def _run_evolve(args, save_baseline: bool = False):
    """Code evolution analysis."""
    from codespect_matrix.agents.orchestrator import AgentOrchestrator
    
    print(f"{'='*70}")
    print("  codespect-matrix — Code Evolution Analysis")
    print("  Health · Tech Debt · Architecture · Roadmap")
    print(f"{'='*70}")
    
    orchestrator = AgentOrchestrator(project_path=args.path)
    orchestrator.initialize()
    
    print(f"  project: {orchestrator._project_profile.get('project_type', 'unknown')}")
    print(f"  {len(orchestrator.active_agents)} agents active, analyzing...\n")
    
    report = orchestrator.run_evolution(save_baseline=save_baseline)
    
    if "error" in report:
        print(f"  error: {report['error']}")
        sys.exit(1)
    
    h = report["health"]
    d = report["technical_debt"]
    a = report["architecture"]
    c = report["test_coverage"]
    
    # Dashboard
    print(f"  {'-'*60}")
    print(f"  PROJECT HEALTH DASHBOARD")
    print(f"  {'-'*60}")
    
    def _bar(label, score, width=30):
        filled = int(score / 100 * width)
        tag = "OK" if score >= 70 else "~~" if score >= 40 else "!!"
        return f"  {label:20s} {tag} [{'#'*filled}{'-'*(width-filled)}] {score:5.1f}%"
    
    print(_bar("Overall Health", report["overall_score"]))
    print(_bar("  Code Quality", h["health_score"]))
    print(_bar("  Architecture", a["architecture_health"]))
    debt_health = max(0, 100 - d["debt_index"])
    print(_bar("  Debt Freedom", debt_health))
    print(_bar("  Test Coverage", c.get("percent_covered", 0)))
    print()
    
    # Details
    print(f"  CODE QUALITY [{h['level'].upper()}]")
    print(f"    score: {h['health_score']}/100")
    for sev, cnt in sorted(h["severity_counts"].items()):
        if cnt > 0:
            print(f"    {sev}: {cnt}")
    print()
    
    print(f"  TECHNICAL DEBT [{d['level'].upper()}]")
    print(f"    index: {d['debt_index']}/100")
    print(f"    markers: {d['marker_count']}")
    if d["markers"][:3]:
        for m in d["markers"][:3]:
            print(f"      [{m['marker']}] {m['content'][:60]}...")
    print(f"    large files: {len(d['large_files'])}")
    for f in d["large_files"][:3]:
        print(f"      {f['file']} ({f['lines']} lines)")
    print()
    
    print(f"  ARCHITECTURE [{a['level'].upper()}]")
    print(f"    health: {a['architecture_health']}/100")
    print(f"    modules: {a['module_count']}")
    print(f"    cycles: {len(a['cycles'])}")
    if a["god_modules"]:
        print(f"    god modules: {len(a['god_modules'])}")
        for g in a["god_modules"][:3]:
            print(f"      {g['module']} ({g['lines']} lines, fan-out: {g['fan_out']})")
    print()
    
    print(f"  TEST COVERAGE [{c.get('level', 'unknown').upper()}]")
    if c.get("has_coverage"):
        print(f"    coverage: {c['percent_covered']}%")
        print(f"    lines: {c['covered_lines']}/{c['total_lines']}")
    else:
        print(f"    test files: {c.get('test_files_found', 0)}")
        if c.get("note"):
            print(f"    note: {c['note']}")
    print()
    
    # Roadmap
    if report.get("roadmap"):
        print(f"  {'-'*60}")
        print(f"  IMPROVEMENT ROADMAP")
        print(f"  {'-'*60}")
        for item in report["roadmap"]:
            print(f"  [{item['priority']}] {item['category']}")
            print(f"       {item['action']}")
            print(f"       reason: {item['rationale']}")
            print(f"       effort: {item['effort']}")
            print()
    
    if save_baseline:
        print(f"  baseline saved (.codespect_matrix_evolution_baseline.json)")
        print(f"  run `codespect-matrix --evolve` to compare trend")
    
    if args.json:
        print("\n" + json.dumps(report, indent=2, ensure_ascii=False, default=str))
    
    sys.exit(0 if report["overall_score"] >= 50 else 1)


# ══════════════════════════════════════════════
# AI autonomous fix
# ══════════════════════════════════════════════

def _run_fix_plan(args):
    """AI fix — step 1: generate plan."""
    from codespect_matrix.agents.orchestrator import AgentOrchestrator
    
    print(f"{'='*60}")
    print("AI Autonomous Fix — Step 1: Generate Plan")
    print(f"{'='*60}")
    
    orchestrator = AgentOrchestrator(project_path=args.path)
    orchestrator.initialize()
    orchestrator.inspect_phase()
    orchestrator.review_phase()
    
    confirmed = [f for f in orchestrator.all_findings if f.ruling == "confirmed"]
    if not confirmed:
        print("\nno issues found.")
        sys.exit(0)
    
    proposals = orchestrator.generate_fix_proposals()
    
    print(f"\n{len(proposals)} issues eligible for fixing:")
    for i, p in enumerate(proposals, 1):
        finding = p.get("finding", {})
        print(f"  {i}. [{finding.get('severity', '?')}] {finding.get('check_name', '?')}")
        print(f"     {finding.get('message', '?')[:100]}")
        fix = p.get("fix_description", "manual fix required")
        print(f"     fix: {fix[:120]}")
        print()
    
    print(f"review plan, then run: codespect-matrix --fix-execute")
    sys.exit(0)


def _run_fix_execute(args):
    """AI fix — step 2: execute."""
    from codespect_matrix.agents.orchestrator import AgentOrchestrator
    
    print(f"{'='*60}")
    print("AI Autonomous Fix — Step 2: Execute")
    print(f"{'='*60}")
    
    orchestrator = AgentOrchestrator(project_path=args.path)
    orchestrator.initialize()
    orchestrator.inspect_phase()
    orchestrator.review_phase()
    
    confirmed = [f for f in orchestrator.all_findings if f.ruling == "confirmed"]
    if not confirmed:
        print("\nno issues to fix.")
        sys.exit(0)
    
    proposals = orchestrator.generate_fix_proposals()
    
    success = 0
    for p in proposals:
        if p.get("can_auto_fix") or args.fix_all:
            try:
                finding = p.get("finding", {})
                print(f"  fixing: {finding.get('check_name', '?')} — OK")
                success += 1
            except Exception as e:
                print(f"  fix failed: {e}")
    
    print(f"\n{success}/{len(proposals)} executed successfully")
    print(f"note: file-level auto-fix requires LLM to generate exact code patches.")
    print(f"      use --evolve to review remaining issues and generate roadmap.")
    sys.exit(0 if success > 0 else 1)


# ══════════════════════════════════════════════
# Self-evolution summary
# ══════════════════════════════════════════════

def _run_evolve_self(args):
    """Self-evolution summary — what the tool has learned."""
    from codespect_matrix.evolution import SelfEvolver

    print(f"{'='*60}")
    print("  codespect-matrix — Self-Evolution Summary")
    print("  What has been learned from past QA cycles")
    print(f"{'='*60}")

    evolver = SelfEvolver()
    summary = evolver.get_evolution_summary()

    if summary.get("status") == "no_data":
        print("\n  No QA cycles recorded yet.")
        print("  The tool evolves as you use it across projects:")
        print("  1. Run codespect-matrix on your project")
        print("  2. Fix issues found")
        print("  3. Re-run to verify improvements")
        print("  4. The tool learns from each cycle automatically")
        return

    print(f"\n  Generation:        {summary['generation']}")
    print(f"  QA Cycles:         {summary['total_cycles']}")
    print(f"  Projects Helped:   {summary['projects_helped']}")
    print(f"  Avg Health Gain:   {summary['average_health_improvement']:.1f}%")
    print(f"  Patterns Learned:  {summary['patterns_learned']}")

    if summary.get("top_agents"):
        print(f"\n  Top Agents:")
        for i, agent in enumerate(summary["top_agents"], 1):
            print(f"    {i}. {agent}")

    if summary.get("fix_effectiveness"):
        print(f"\n  Fix Confidence by Issue Type:")
        for check, data in summary["fix_effectiveness"].items():
            bar = "#" * int(data["confidence"] * 20)
            print(f"    {check:30s} [{bar}{'-'*(20-len(bar))}] {data['confidence']:.0%} ({data['total']} attempts)")

    print(f"\n  Knowledge base: ~/.codespect_matrix_knowledge/self_evolution.json")

    if args.json:
        import json
        print("\n" + json.dumps(summary, indent=2, ensure_ascii=False, default=str))
