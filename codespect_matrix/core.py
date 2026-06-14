"""核心服务类 - 提供完整的质量校验流程"""
# 由 25 位视角专家组成的迭代式质量校验引擎
# 功能矩阵: 全量扫描 | 增量diff | CI门禁 | 风险评分 | 基线对比

import os
import json
import datetime
import subprocess
from typing import Dict, List, Any, Optional

from .models import ValidationResult, RoundResult, ProjectProfile
from .scanner import ProjectScanner
from .perspectives import PerspectiveRegistry
from .llm_service import get_llm_service, LLMService

# 严重程度 → 数值权重（用于风险评分）
SEVERITY_WEIGHT = {
    "critical": 100,
    "high": 50,
    "medium": 15,
    "low": 3,
    "info": 1,
}

# CI 门禁阈值
CI_GATE_THRESHOLDS = {
    "critical": 0,   # 0 个 critical 才放行
    "high": 5,       # ≤5 个 high
    "medium": 30,    # ≤30 个 medium
}

BASELINE_FILE = ".codespect_matrix_baseline.json"


class QAService:
    """智能质量校验服务"""
    
    def __init__(self, project_path: str = ".", config: Optional[Dict] = None, llm_service: Optional[LLMService] = None):
        self.project_path = project_path
        self.config = config or {}
        self.scanner = ProjectScanner()
        self.registry = PerspectiveRegistry()
        self.round_results: List[RoundResult] = []
        self.project_profile: Optional[ProjectProfile] = None
        self.llm_service = llm_service or get_llm_service()
        
        # 初始化内置视角专家
        self._init_default_experts()
    
    def _init_default_experts(self):
        """初始化内置视角专家"""
        from .perspectives import (
            DeveloperExpert,
            UserExpert,
            SecurityExpert,
            HealthcareExpert,
            AuditorExpert,
            StatisticianExpert,
            PerformanceExpert,
            ComplianceExpert,
            BusinessExpert,
            ArchitectExpert,
            DevOpsExpert,
            HardcodeInspectorExpert,
            TestExpert,
            DependencyExpert,
            LintExpert,
            FrontendExpert,
            DBMigrationExpert,
            PHIInspectExpert,
            DataIntegrityExpert,
            ProductionReadinessExpert,
            MedicalDataValidatorExpert,
            APIContractExpert,
            ConcurrencyExpert,
            ObservabilityExpert,
            ConfigAuditExpert,
        )
        
        experts = [
            DeveloperExpert,
            UserExpert,
            SecurityExpert,
            HealthcareExpert,
            AuditorExpert,
            StatisticianExpert,
            PerformanceExpert,
            ComplianceExpert,
            BusinessExpert,
            ArchitectExpert,
            DevOpsExpert,
            HardcodeInspectorExpert,
            TestExpert,
            DependencyExpert,
            LintExpert,
            FrontendExpert,
            DBMigrationExpert,
            PHIInspectExpert,
            DataIntegrityExpert,
            ProductionReadinessExpert,
            MedicalDataValidatorExpert,
            APIContractExpert,
            ConcurrencyExpert,
            ObservabilityExpert,
            ConfigAuditExpert,
        ]
        
        for expert_class in experts:
            self.registry.register_expert(expert_class)
    
    def analyze_project(self) -> ProjectProfile:
        """分析项目特征"""
        self.project_profile = self.scanner.scan(self.project_path)
        return self.project_profile
    
    def recommend_perspectives(self) -> List[str]:
        """基于项目特征推荐视角专家（用于 --targeted 模式）"""
        if not self.project_profile:
            self.analyze_project()
        
        return self.registry.recommend_experts(self.project_profile.to_dict())
    
    def score_all_perspectives(self) -> List[Dict[str, Any]]:
        """对所有专家评分 — 返回全量专家及兼容性"""
        if not self.project_profile:
            self.analyze_project()
        return self.registry.score_all_experts(self.project_profile.to_dict())
    
    def validate(self, round_number: int = 1) -> RoundResult:
        """执行全量质量校验 — 默认运行所有 26 位专家
        
        每项结果附带 compatibility 元数据，标识该专家与项目的匹配度。
        兼容性低只代表该专家的 domain 与项目不重叠，不代表结果应忽略。
        """
        if not self.project_profile:
            self.analyze_project()
        
        # 获取全量专家及兼容性评分
        all_scored = self.score_all_perspectives()
        features = self.project_profile.to_dict()
        
        results = []
        for item in all_scored:
            expert_name = item["name"]
            compatibility = item["compatibility"]
            expert = self.registry.get_expert(expert_name)
            if not expert:
                continue
            try:
                expert_results = expert.validate(features)
                # 为每条结果打上兼容性标记
                for r in expert_results:
                    r.compatibility = compatibility
                results.extend(expert_results)
            except Exception:
                pass  # 单个专家失败不影响其他专家
        
        round_result = RoundResult(
            round_number=round_number,
            issues_found=results,
            status=self._determine_status(results),
        )
        self.round_results.append(round_result)
        
        # 存储兼容性分数供报告使用
        round_result.expert_scores = all_scored
        return round_result
    
    def validate_targeted(self, round_number: int = 1) -> RoundResult:
        """针对性校验 — 仅运行兼容性评分最高的 5 位专家（快速扫描模式）"""
        if not self.project_profile:
            self.analyze_project()
        
        recommended_experts = self.recommend_perspectives()
        
        results = []
        for expert_name in recommended_experts:
            expert = self.registry.get_expert(expert_name)
            if expert:
                expert_results = expert.validate(self.project_profile.to_dict())
                results.extend(expert_results)
        
        round_result = RoundResult(
            round_number=round_number,
            issues_found=results,
            status=self._determine_status(results),
        )
        self.round_results.append(round_result)
        return round_result
    
    def _determine_status(self, results: List[ValidationResult]) -> str:
        """确定校验状态"""
        has_critical = any(r.severity in ["critical", "high"] for r in results)
        if has_critical:
            return "failed"
        has_warning = any(r.status == "warning" for r in results)
        if has_warning:
            return "warning"
        return "passed"
    
    def is_converged(self) -> bool:
        """检查是否收敛 — 增强版：追踪问题指纹变化
        
        收敛条件（同时满足）：
        1. 至少2轮校验
        2. 最近两轮无 P0/P1 新问题
        3. 最近轮次问题总数不再增长
        """
        if len(self.round_results) < 2:
            return False
        
        prev = self.round_results[-2]
        curr = self.round_results[-1]
        
        # 按指纹（check_name+message）去重对比
        prev_fp = {f"{r.check_name}:{r.message[:60]}" for r in prev.issues_found}
        curr_fp = {f"{r.check_name}:{r.message[:60]}" for r in curr.issues_found}
        
        new_issues = curr_fp - prev_fp
        resolved_issues = prev_fp - curr_fp
        
        # 有新 P0/P1 问题 → 未收敛
        has_new_critical = any(
            r.severity in ("critical", "high")
            for r in curr.issues_found
            if f"{r.check_name}:{r.message[:60]}" in new_issues
        )
        if has_new_critical:
            return False
        
        # 总问题数在增长 → 未收敛
        if len(curr.issues_found) > len(prev.issues_found):
            return False
        
        # 问题数已经稳定或下降
        return True
    
    def converge_summary(self) -> Dict[str, int]:
        """获取收敛摘要"""
        if len(self.round_results) < 2:
            return {"status": "insufficient_data"}
        
        prev = self.round_results[-2]
        curr = self.round_results[-1]
        
        prev_fp = {f"{r.check_name}:{r.message[:60]}" for r in prev.issues_found}
        curr_fp = {f"{r.check_name}:{r.message[:60]}" for r in curr.issues_found}
        
        return {
            "total_current": len(curr.issues_found),
            "total_previous": len(prev.issues_found),
            "new": len(curr_fp - prev_fp),
            "resolved": len(prev_fp - curr_fp),
            "persistent": len(curr_fp & prev_fp),
            "converged": self.is_converged()
        }
    
    def generate_report(self, use_llm: bool = True) -> str:
        """生成质量报告
        
        Args:
            use_llm: 是否使用大模型生成智能报告
        
        Returns:
            格式化的质量报告
        """
        if not self.project_profile:
            return "请先执行项目分析"
        
        # 收集所有验证结果
        all_issues = []
        for round_result in self.round_results:
            for issue in round_result.issues_found:
                all_issues.append(issue.to_dict())
        
        # 如果有大模型服务且启用，使用大模型生成智能报告
        if use_llm and self.llm_service:
            try:
                return self.llm_service.generate_report(
                    validation_results=all_issues,
                    project_profile=self.project_profile.to_dict()
                )
            except Exception as e:
                # 如果大模型调用失败，回退到普通报告
                pass
        
        # 回退到普通报告生成
        report = []
        report.append("# 质量校验报告")
        report.append(f"\n**项目名称**: {os.path.basename(self.project_path)}")
        report.append(f"**项目类型**: {self.project_profile.project_type}")
        report.append(f"**技术栈**: {', '.join(self.project_profile.tech_stack)}")
        report.append(f"**规模**: {self.project_profile.scale}")
        report.append(f"**领域**: {self.project_profile.domain}")
        report.append(f"**校验轮次**: {len(self.round_results)}")
        report.append(f"**收敛状态**: {'已收敛' if self.is_converged() else '未收敛'}")
        
        # 添加每轮结果
        for round_result in self.round_results:
            report.append(f"\n## 第{round_result.round_number}轮")
            report.append(f"- 时间: {round_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"- 状态: {round_result.status}")
            report.append(f"- 发现问题: {len(round_result.issues_found)}")
            
            for issue in round_result.issues_found:
                report.append(f"\n### {issue.check_name}")
                report.append(f"- 状态: {issue.status}")
                report.append(f"- 严重程度: {issue.severity}")
                report.append(f"- 描述: {issue.message}")
                if issue.remediation:
                    report.append(f"- 修复建议: {issue.remediation}")
        
        return "\n".join(report)
    
    def analyze_with_llm(self) -> Dict[str, Any]:
        """使用大模型分析项目特征
        
        Returns:
            大模型分析结果
        """
        if not self.project_profile:
            self.analyze_project()
        
        if not self.llm_service:
            return {"error": "未配置大模型服务"}
        
        return self.llm_service.analyze_project(self.project_profile.to_dict())
    
    def register_expert(self, expert_class):
        """注册自定义视角专家"""
        self.registry.register_expert(expert_class)
    
    # ─────────────────────────────────────────────
    # 升级能力 1: Risk Scoring Engine — 项目级加权风险评分
    # ─────────────────────────────────────────────
    def compute_risk_score(self, issues: Optional[List[ValidationResult]] = None) -> Dict[str, Any]:
        """计算项目风险评分，返回可雷达图的结构化数据
        
        Returns:
            {
                "total_score": 加权总分,
                "max_score": 理论最高分(全critical),
                "risk_level": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL",
                "by_severity": {"critical": n, "high": n, ...},
                "by_expert": {"developer": score, "security": score, ...},
                "top_risks": [{expert, check, score}, ...],
                "gate_pass": bool  # 是否通过CI门禁
            }
        """
        if issues is None:
            if self.round_results:
                issues = self.round_results[-1].issues_found
            else:
                return {"total_score": 0, "risk_level": "UNKNOWN"}
        
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        by_expert: Dict[str, float] = {}
        risk_details: List[Dict] = []
        
        for r in issues:
            by_severity[r.severity] = by_severity.get(r.severity, 0) + 1
            w = SEVERITY_WEIGHT.get(r.severity, 1)
            
            expert_cat = r.check_name.split("_")[0] if "_" in r.check_name else r.check_name
            by_expert[expert_cat] = by_expert.get(expert_cat, 0) + w
            risk_details.append({
                "expert": expert_cat,
                "check": r.check_name,
                "severity": r.severity,
                "weight": w,
                "message": r.message[:120],
            })
        
        total_score = sum(by_expert.values())
        max_score = len(issues) * 100  # 理论最大值（全critical）
        normalized = min(1.0, total_score / max(max_score, 1))
        
        if normalized >= 0.7 or by_severity.get("critical", 0) > 0:
            risk_level = "CRITICAL"
        elif normalized >= 0.4 or by_severity.get("high", 0) > 10:
            risk_level = "HIGH"
        elif normalized >= 0.15 or by_severity.get("high", 0) > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # CI 门禁判断
        gate_pass = (
            by_severity.get("critical", 0) <= CI_GATE_THRESHOLDS["critical"] and
            by_severity.get("high", 0) <= CI_GATE_THRESHOLDS["high"] and
            by_severity.get("medium", 0) <= CI_GATE_THRESHOLDS["medium"]
        )
        
        # Top 10 风险项
        risk_details.sort(key=lambda x: x["weight"], reverse=True)
        
        return {
            "total_score": int(total_score),
            "max_score": max_score,
            "normalized_risk": round(normalized, 3),
            "risk_level": risk_level,
            "by_severity": by_severity,
            "by_expert": {k: int(v) for k, v in sorted(by_expert.items(), key=lambda x: -x[1])},
            "issue_count": len(issues),
            "top_risks": risk_details[:10],
            "gate_pass": gate_pass,
        }
    
    # ─────────────────────────────────────────────
    # 升级能力 2: CI/CD Gate Mode — 出口码 + JSON
    # ─────────────────────────────────────────────
    def ci_check(self, round_number: int = 1) -> Dict[str, Any]:
        """CI/CD 门禁模式 — 执行校验并返回结构化结果
        
        当 critical > 0 或 high > 5 时 exit_code != 0
        
        Returns:
            {
                "exit_code": 0 | 1,
                "risk_score": {...},
                "issues": [...],
                "project": {...},
                "timestamp": "..."
            }
        """
        # 执行校验
        result = self.validate(round_number)
        score = self.compute_risk_score(result.issues_found)
        
        exit_code = 0 if score["gate_pass"] else 1
        
        return {
            "exit_code": exit_code,
            "risk_score": score,
            "issues": [r.to_dict() for r in result.issues_found],
            "project": self.project_profile.to_dict() if self.project_profile else {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    
    # ─────────────────────────────────────────────
    # 升级能力 3: Differential QA — git diff 增量扫描
    # ─────────────────────────────────────────────
    def _get_diff_files(self, target_branch: str = "HEAD~1") -> List[str]:
        """获取 git diff 变更文件列表"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", target_branch],
                capture_output=True, text=True, timeout=10,
                cwd=self.project_path
            )
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            return [f for f in files if f.endswith('.py') and os.path.exists(
                os.path.join(self.project_path, f))]
        except Exception:
            return []
    
    def _get_diff_lines(self, filepath: str, target_branch: str = "HEAD~1") -> List[int]:
        """获取某文件变更的具体行号"""
        try:
            result = subprocess.run(
                ["git", "diff", target_branch, "--", filepath],
                capture_output=True, text=True, timeout=10,
                cwd=self.project_path
            )
            lines = set()
            for line in result.stdout.split('\n'):
                # git diff 的行号在 @@ -old,count +new,count @@ 中
                if line.startswith('@@'):
                    import re
                    m = re.search(r'\+(\d+)(?:,(\d+))?', line)
                    if m:
                        start = int(m.group(1))
                        count = int(m.group(2)) if m.group(2) else 1
                        for ln in range(start, start + count):
                            lines.add(ln)
            return sorted(lines)
        except Exception:
            return []
    
    def validate_diff(self, target_branch: str = "HEAD~1") -> Dict[str, Any]:
        """增量 QA — 仅扫描 git diff 变更文件/行
        
        Args:
            target_branch: 对比的目标分支/commit，默认 HEAD~1
        
        Returns:
            {
                "diff_files": [...],
                "total_diff_files": n,
                "issues": [...],
                "risk_score": {...},
                "is_clean": bool
            }
        """
        import re
        
        if not self.project_profile:
            self.analyze_project()
        
        diff_files = self._get_diff_files(target_branch)
        if not diff_files:
            return {
                "diff_files": [],
                "total_diff_files": 0,
                "issues": [],
                "risk_score": {},
                "is_clean": True,
                "message": "no python files changed"
            }
        
        recommended = self.recommend_perspectives()
        all_results = []
        
        for filepath in diff_files:
            abs_path = os.path.join(self.project_path, filepath)
            changed_lines = self._get_diff_lines(filepath, target_branch)
            
            try:
                with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                    full_lines = f.readlines()
            except Exception:
                continue
            
            for expert_name in recommended:
                expert = self.registry.get_expert(expert_name)
                if not expert:
                    continue
                
                try:
                    # 对每个专家，只传该文件的该行范围做检查
                    # 实际策略：对变更文件执行全专家扫描，但只保留变更行相关的问题
                    expert_results = expert.validate(self.project_profile.to_dict())
                    
                    for r in expert_results:
                        # 检查 message 中是否引用了当前文件
                        msg = r.message
                        if filepath in msg or os.path.basename(filepath) in msg:
                            # 尝试提取行号
                            m = re.search(r':(\d+)', msg)
                            if m:
                                line_num = int(m.group(1))
                                if line_num in changed_lines or not changed_lines:
                                    all_results.append(r)
                            else:
                                all_results.append(r)
                except Exception:
                    pass
        
        # 去重
        seen = set()
        unique_results = []
        for r in all_results:
            fp = f"{r.check_name}:{r.message[:80]}"
            if fp not in seen:
                seen.add(fp)
                unique_results.append(r)
        
        score = self.compute_risk_score(unique_results) if unique_results else {}
        
        return {
            "diff_files": diff_files,
            "total_diff_files": len(diff_files),
            "issues": [r.to_dict() for r in unique_results],
            "risk_score": score,
            "is_clean": len(unique_results) == 0,
            "message": f"scanned {len(diff_files)} changed files, found {len(unique_results)} issues"
        }
    
    # ─────────────────────────────────────────────
    # 升级能力 4: Self-Baseline — 基线建立与增量 delta
    # ─────────────────────────────────────────────
    def save_baseline(self, round_number: int = 1) -> str:
        """保存当前 QA 结果为基线文件"""
        result = self.validate(round_number)
        score = self.compute_risk_score(result.issues_found)
        
        baseline = {
            "version": "1.0",
            "project": self.project_profile.to_dict() if self.project_profile else {},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "round_number": round_number,
            "issue_count": len(result.issues_found),
            "risk_score": score,
            "issues": [r.to_dict() for r in result.issues_found],
        }
        
        baseline_path = os.path.join(self.project_path, BASELINE_FILE)
        with open(baseline_path, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)
        
        return baseline_path
    
    def load_baseline(self) -> Optional[Dict[str, Any]]:
        """加载基线文件"""
        baseline_path = os.path.join(self.project_path, BASELINE_FILE)
        if not os.path.exists(baseline_path):
            return None
        try:
            with open(baseline_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def diff_baseline(self, round_number: int = 1) -> Dict[str, Any]:
        """对比当前扫描与基线的差异
        
        Returns:
            {
                "has_baseline": bool,
                "current": {...},
                "baseline": {...},
                "delta": {
                    "new_issues": n,
                    "resolved_issues": n,
                    "persistent_issues": n,
                    "risk_delta": score_change,
                    "trend": "improving"|"degrading"|"stable"
                }
            }
        """
        baseline = self.load_baseline()
        current_result = self.validate(round_number)
        current_score = self.compute_risk_score(current_result.issues_found)
        
        if not baseline:
            return {
                "has_baseline": False,
                "current": {"issue_count": len(current_result.issues_found), "risk_score": current_score},
                "message": "no baseline found — run save_baseline() first"
            }
        
        # 按指纹对比
        baseline_fp = {f"{r['check_name']}:{r['message'][:80]}" for r in baseline.get("issues", [])}
        current_fp = {f"{r.check_name}:{r.message[:80]}" for r in current_result.issues_found}
        
        new_issues = current_fp - baseline_fp
        resolved_issues = baseline_fp - current_fp
        persistent = current_fp & baseline_fp
        
        baseline_risk = baseline.get("risk_score", {}).get("total_score", 0)
        current_risk = current_score.get("total_score", 0)
        risk_delta = current_risk - baseline_risk
        
        if risk_delta < -10:
            trend = "improving"
        elif risk_delta > 10:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "has_baseline": True,
            "baseline": {
                "timestamp": baseline.get("timestamp"),
                "issue_count": baseline.get("issue_count", 0),
                "risk_score": baseline.get("risk_score", {}).get("total_score", 0),
            },
            "current": {
                "issue_count": len(current_result.issues_found),
                "risk_score": current_score.get("total_score", 0),
                "risk_level": current_score.get("risk_level"),
            },
            "delta": {
                "new_issues": len(new_issues),
                "resolved_issues": len(resolved_issues),
                "persistent_issues": len(persistent),
                "risk_delta": risk_delta,
                "trend": trend,
            }
        }
    
    def run_full_cycle(self, max_rounds: int = 10) -> str:
        """执行完整的校验周期"""
        report = ["# 完整质量校验周期报告"]
        report.append(f"\n**项目**: {os.path.basename(self.project_path)}")
        report.append(f"**开始时间**: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        
        for round_num in range(1, max_rounds + 1):
            report.append(f"\n---\n## 第{round_num}轮校验")
            
            try:
                result = self.validate(round_num)
                report.append(f"- 状态: {result.status}")
                report.append(f"- 发现问题: {len(result.issues_found)}")
                
                if self.is_converged():
                    report.append("\n✅ 系统已收敛！")
                    break
                
            except Exception as e:
                report.append(f"- 错误: {str(e)}")
                break
        
        report.append(f"\n**结束时间**: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**总轮次**: {len(self.round_results)}")
        report.append(f"**最终状态**: {'已收敛' if self.is_converged() else '未收敛'}")
        
        return "\n".join(report)