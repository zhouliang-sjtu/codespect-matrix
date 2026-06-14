"""命令行接口 - 提供交互式质量校验功能"""

import argparse
import json
import sys
from typing import Optional

from codespect_matrix import QAService

# 严重度排序权重（用于结果展示）
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def main():
    parser = argparse.ArgumentParser(
        prog="codespect-matrix",
        description="AI驱动的智能质量校验引擎 — 25专家 × 5能力 × 全链路覆盖",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行全量质量校验（默认）
    codespect-matrix --round 1
    
    # 快速扫描模式（仅 top-5 专家）
    codespect-matrix --targeted
  
  # CI/CD 门禁模式（GitHub Actions / Jenkins）
  codespect-matrix --ci --json
  
  # 增量校验（仅扫描 git diff 变更文件）
  codespect-matrix --diff
  
  # 建立基线
  codespect-matrix --baseline
  
  # 对比基线变化
  codespect-matrix --baseline-diff
  
  # 风险评分
  codespect-matrix --risk-score
  
  # 完整校验周期
  codespect-matrix --full-cycle
  
  # 生成详细报告
  codespect-matrix --report --output report.md
        """
    )
    
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="项目路径 (默认: 当前目录)"
    )
    
    parser.add_argument(
        "--round", "-r",
        type=int,
        default=1,
        help="校验轮次 (默认: 1)"
    )
    
    parser.add_argument(
        "--full-cycle", "-f",
        action="store_true",
        help="执行完整校验周期直到收敛"
    )
    
    parser.add_argument(
        "--analyze", "-a",
        action="store_true",
        help="仅分析项目特征并推荐专家"
    )
    
    parser.add_argument(
        "--report", "-o",
        action="store_true",
        help="生成质量报告"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="报告输出文件路径"
    )
    
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=10,
        help="最大校验轮次 (默认: 10)"
    )
    
    # ── 新增：上游能力 ──
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI/CD 门禁模式 — 严重问题超标时 exit_code=1"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式（配合 --ci 或 --risk-score 使用）"
    )
    
    parser.add_argument(
        "--diff",
        type=str,
        nargs='?',
        const="HEAD~1",
        metavar="TARGET",
        help="增量校验 — 仅扫描 git diff 变更文件 (默认对比 HEAD~1)"
    )
    
    parser.add_argument(
        "--targeted",
        action="store_true",
        help="快速扫描模式 — 仅运行兼容性最高的 5 位专家（默认运行全部 26 位）"
    )
    
    parser.add_argument(
        "--risk-score",
        action="store_true",
        help="计算项目风险评分"
    )
    
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="保存当前 QA 结果为基线 (.codespect_matrix_baseline.json)"
    )
    
    parser.add_argument(
        "--baseline-diff",
        action="store_true",
        help="对比当前扫描与基线的差异"
    )
    
    args = parser.parse_args()
    
    try:
        qa_service = QAService(project_path=args.path)
        
        # ── CI 门禁模式 ──
        if args.ci:
            result = qa_service.ci_check(round_number=args.round)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                score = result["risk_score"]
                print(f"{'='*60}")
                print(f"CI Gate Check — {'PASS' if result['exit_code']==0 else 'FAIL'}")
                print(f"{'='*60}")
                print(f"风险等级: {score.get('risk_level', 'N/A')}")
                print(f"风险评分: {score.get('total_score', 0)}")
                print(f"严重分布: {score.get('by_severity', {})}")
                print(f"问题总数: {score.get('issue_count', 0)}")
                print(f"门禁状态: {'✅ 通过' if score.get('gate_pass') else '❌ 未通过'}")
            sys.exit(result["exit_code"])
        
        # ── 增量校验模式 ──
        if args.diff is not None:
            target = args.diff if args.diff != "HEAD~1" else args.diff
            result = qa_service.validate_diff(target_branch=target)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"{'='*60}")
                print(f"增量校验 — git diff {target}")
                print(f"{'='*60}")
                print(f"变更文件数: {result['total_diff_files']}")
                if result.get("issues"):
                    print(f"发现问题: {len(result['issues'])}")
                    score = result.get("risk_score", {})
                    if score:
                        print(f"风险等级: {score.get('risk_level', 'N/A')}")
                    for issue in result["issues"][:20]:
                        print(f"\n  [{issue['severity'].upper()}] {issue['check_name']}")
                        print(f"    描述: {issue['message']}")
                        if issue.get('remediation'):
                            print(f"    修复: {issue['remediation']}")
                else:
                    print("状态: ✅ 无新增问题")
            sys.exit(0 if result.get("is_clean") else 1)
        
        # ── 风险评分模式 ──
        if args.risk_score:
            qa_service.analyze_project()
            result = qa_service.validate(args.round)
            score = qa_service.compute_risk_score(result.issues_found)
            if args.json:
                print(json.dumps(score, indent=2, ensure_ascii=False))
            else:
                print(f"{'='*60}")
                print(f"项目风险评分")
                print(f"{'='*60}")
                print(f"风险等级: {score['risk_level']}")
                print(f"加权总分: {score['total_score']} / {score['max_score']}")
                print(f"归一化风险: {score['normalized_risk']}")
                print(f"问题总数: {score['issue_count']}")
                print(f"\n按严重度分布:")
                for sev, cnt in score['by_severity'].items():
                    if cnt > 0:
                        print(f"  {sev}: {cnt}")
                print(f"\n按专家领域分布 (Top 10):")
                for i, (expert, s) in enumerate(list(score['by_expert'].items())[:10]):
                    print(f"  {expert}: {s}")
                print(f"\n最高风险项 (Top 5):")
                for r in score['top_risks'][:5]:
                    print(f"  [{r['severity'].upper()}] {r['expert']}/{r['check']}: {r['message'][:100]}")
                print(f"\nCI 门禁: {'✅ 通过' if score['gate_pass'] else '❌ 未通过'}")
            sys.exit(0)
        
        # ── 基线模式 ──
        if args.baseline:
            baseline_path = qa_service.save_baseline(round_number=args.round)
            print(f"{'='*60}")
            print(f"基线已建立")
            print(f"{'='*60}")
            print(f"文件: {baseline_path}")
            score = qa_service.compute_risk_score()
            print(f"风险等级: {score.get('risk_level', 'N/A')}")
            print(f"问题总数: {score.get('issue_count', 0)}")
            print(f"\n后续运行 `codespect-matrix --baseline-diff` 可对比变化")
            sys.exit(0)
        
        # ── 基线对比模式 ──
        if args.baseline_diff:
            result = qa_service.diff_baseline(round_number=args.round)
            if args.json:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                if not result["has_baseline"]:
                    print("❌ 未找到基线文件。请先运行 `codespect-matrix --baseline`")
                else:
                    delta = result["delta"]
                    trend_icon = {"improving": "⬇ 改善", "degrading": "⬆ 恶化", "stable": "→ 稳定"}
                    print(f"{'='*60}")
                    print(f"基线对比")
                    print(f"{'='*60}")
                    print(f"基线时间: {result['baseline']['timestamp']}")
                    print(f"基线风险评分: {result['baseline']['risk_score']} → 当前: {result['current']['risk_score']}")
                    print(f"趋势: {trend_icon.get(delta['trend'], delta['trend'])}")
                    print(f"\n变化:")
                    print(f"  新增问题: {delta['new_issues']}")
                    print(f"  已解决问题: {delta['resolved_issues']}")
                    print(f"  持续存在问题: {delta['persistent_issues']}")
                    print(f"  风险变化: {delta['risk_delta']:+d}")
            sys.exit(0)
        
        # ── 原有模式 ──
        if args.analyze:
            profile = qa_service.analyze_project()
            print("=" * 60)
            print("项目特征分析结果")
            print("=" * 60)
            print(f"项目类型: {profile.project_type}")
            print(f"技术栈: {', '.join(profile.tech_stack)}")
            print(f"规模: {profile.scale}")
            print(f"复杂度: {profile.complexity}")
            print(f"领域: {profile.domain}")
            print(f"安全要求: {profile.security_requirements}/10")
            print(f"文件数量: {profile.file_count}")
            print(f"代码行数: {profile.lines_of_code}")
            print("=" * 60)
            
            perspectives = qa_service.recommend_perspectives()
            print("\n推荐视角专家:")
            for i, perspective in enumerate(perspectives, 1):
                print(f"  {i}. {perspective}")
            
        elif args.full_cycle:
            print("=" * 60)
            print("开始完整校验周期")
            print("=" * 60)
            
            report = qa_service.run_full_cycle(max_rounds=args.max_rounds)
            print(report)
            
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(report)
                print(f"\n报告已保存到: {args.output}")
        
        else:
            # 默认：全量扫描
            use_targeted = args.targeted
            
            print(f"{'='*60}")
            if use_targeted:
                print(f"快速扫描模式 — 第 {args.round} 轮（仅 top-5 专家）")
            else:
                print(f"全量扫描模式 — 第 {args.round} 轮（全部 26 位专家）")
            print(f"{'='*60}")
            
            if use_targeted:
                result = qa_service.validate_targeted(round_number=args.round)
            else:
                result = qa_service.validate(round_number=args.round)
            
            print(f"\n校验状态: {result.status}")
            print(f"发现问题: {len(result.issues_found)}")
            
            # 全量模式下显示专家兼容性概览
            if not use_targeted and hasattr(result, 'expert_scores') and result.expert_scores:
                scores = result.expert_scores
                high_compat = [s for s in scores if s['compatibility'] >= 0.7]
                low_compat = [s for s in scores if s['compatibility'] < 0.3]
                print(f"\n专家匹配度:")
                if high_compat:
                    print(f"  高匹配 (≥0.7): {', '.join(s['name'] for s in high_compat)}")
                if low_compat:
                    print(f"  低匹配 (<0.3): {', '.join(s['name'] for s in low_compat)}")
                print(f"  (低匹配专家的发现同样有效，仅代表领域不完全重叠)")
            
            if result.issues_found:
                print(f"\n问题详情 (按严重度排序):")
                for issue in sorted(result.issues_found, key=lambda r: SEVERITY_ORDER.get(r.severity, 99)):
                    compat_tag = ""
                    if not use_targeted and hasattr(issue, 'compatibility') and issue.compatibility is not None:
                        if issue.compatibility < 0.3:
                            compat_tag = " [低匹配]"  # 仍然显示，但标记
                    print(f"\n  [{issue.severity.upper()}]{compat_tag} {issue.check_name}")
                    print(f"    状态: {issue.status}")
                    print(f"    描述: {issue.message}")
                    if issue.remediation:
                        print(f"    修复建议: {issue.remediation}")
            
            if args.report:
                report = qa_service.generate_report()
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        f.write(report)
                    print(f"\n报告已保存到: {args.output}")
                else:
                    print("\n" + "=" * 60)
                    print("质量报告")
                    print("=" * 60)
                    print(report)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()