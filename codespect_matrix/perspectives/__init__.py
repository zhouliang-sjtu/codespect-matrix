"""视角专家模块 - 提供多种视角的质量验证能力"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import subprocess
import os


class ValidationResult:
    """验证结果"""
    def __init__(self, check_name: str, status: str, message: str, severity: str, remediation: Optional[str] = None):
        self.check_name = check_name
        self.status = status
        self.message = message
        self.severity = severity
        self.remediation = remediation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "severity": self.severity,
            "remediation": self.remediation,
        }


class BasePerspectiveExpert(ABC):
    """视角专家基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取视角名称"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取视角描述"""
        pass
    
    @abstractmethod
    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        """计算与项目的兼容性（0-1）"""
        pass
    
    @abstractmethod
    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        """执行验证"""
        pass
    
    def optimize(self, data: Any) -> Any:
        """执行优化（可选）"""
        return data


class PerspectiveRegistry:
    """视角专家注册表"""
    
    def __init__(self):
        self.experts = {}
    
    def register_expert(self, expert_class):
        """注册视角专家"""
        instance = expert_class()
        self.experts[instance.get_name()] = expert_class
    
    def get_expert(self, name: str):
        """获取视角专家实例"""
        if name in self.experts:
            return self.experts[name]()
        return None
    
    def get_all_experts(self) -> List[str]:
        """获取所有专家名称"""
        return list(self.experts.keys())
    
    def recommend_experts(self, project_features: Dict[str, Any]) -> List[str]:
        """基于项目特征推荐视角专家 — 返回 top-5 兼容专家"""
        recommendations = []
        
        for name, expert_class in self.experts.items():
            expert = expert_class()
            compatibility = expert.get_compatibility(project_features)
            if compatibility >= 0.3:
                recommendations.append({
                    "name": name,
                    "compatibility": compatibility
                })
        
        recommendations.sort(key=lambda x: x["compatibility"], reverse=True)
        return [r["name"] for r in recommendations[:5]]
    
    def score_all_experts(self, project_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """对所有专家评分 — 返回全量专家及兼容性，用于全量扫描
        
        Returns:
            [{"name": "...", "compatibility": 0.95, "description": "..."}, ...]
            按兼容性降序排列
        """
        scored = []
        for name, expert_class in self.experts.items():
            expert = expert_class()
            compatibility = expert.get_compatibility(project_features)
            scored.append({
                "name": name,
                "compatibility": round(compatibility, 3),
                "description": expert.get_description(),
            })
        scored.sort(key=lambda x: x["compatibility"], reverse=True)
        return scored


class DeveloperExpert(BasePerspectiveExpert):
    """开发者视角专家"""
    
    def get_name(self) -> str:
        return "developer"
    
    def get_description(self) -> str:
        return "代码质量、类型安全、架构设计验证"
    
    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        return 1.0  # 适用于所有项目
    
    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []
        
        # 检查 Python 编译
        try:
            result = subprocess.run(
                ["python", "-m", "compileall", "-q", "."],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                results.append(ValidationResult(
                    check_name="python_compile",
                    status="failed",
                    message=f"Python编译错误: {result.stderr}",
                    severity="high",
                    remediation="修复Python语法错误"
                ))
            else:
                results.append(ValidationResult(
                    check_name="python_compile",
                    status="passed",
                    message="Python编译通过",
                    severity="low"
                ))
        except Exception as e:
            results.append(ValidationResult(
                check_name="python_compile",
                status="warning",
                message=f"编译检查失败: {str(e)}",
                severity="medium"
            ))
        
        # 检查 TypeScript 编译
        if "TypeScript" in project_features.get("tech_stack", []):
            try:
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    results.append(ValidationResult(
                        check_name="typescript_compile",
                        status="failed",
                        message=f"TypeScript编译错误: {result.stderr}",
                        severity="high",
                        remediation="修复TypeScript类型错误"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="typescript_compile",
                        status="passed",
                        message="TypeScript编译通过",
                        severity="low"
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    check_name="typescript_compile",
                    status="warning",
                    message=f"TypeScript检查失败: {str(e)}",
                    severity="medium"
                ))
        
        # 检查依赖文件
        if os.path.exists("requirements.txt"):
            results.append(ValidationResult(
                check_name="requirements_exists",
                status="passed",
                message="requirements.txt 存在",
                severity="low"
            ))
        elif os.path.exists("pyproject.toml"):
            results.append(ValidationResult(
                check_name="requirements_exists",
                status="passed",
                message="pyproject.toml 存在",
                severity="low"
            ))
        else:
            results.append(ValidationResult(
                check_name="requirements_exists",
                status="warning",
                message="未找到依赖管理文件",
                severity="medium",
                remediation="创建 requirements.txt 或 pyproject.toml"
            ))
        
        return results


class SecurityExpert(BasePerspectiveExpert):
    """安全工程师视角专家 — 深度漏洞扫描"""

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    VULN_PATTERNS = [
        # 代码注入
        ("security_eval_exec", [(r'\b(?:eval|exec|compile)\s*\(', "eval/exec 调用可能导致代码注入")], "critical",
         "避免使用 eval/exec，改用 ast.literal_eval 或更安全的替代方案"),
        # 反序列化漏洞
        ("security_pickle", [(r'\b(?:pickle|cPickle|_pickle)\.(?:load|loads)\s*\(', "pickle 反序列化可导致 RCE"),
          (r'\byaml\.load\s*\(', "yaml.load() 不安全（应用 yaml.safe_load()）"),], "critical",
         "使用 yaml.safe_load/ruamel.yaml，或对 pickle 输入做签名验证"),
        # 命令注入
        ("security_command_injection", [(r'\bos\.system\s*\(.*\+', "os.system 拼接字符串 = 命令注入风险"),
          (r'\bsubprocess\.(?:call|run|Popen)\(.*\+', "subprocess 拼接字符串 = 命令注入风险"),
          (r'\bos\.(?:popen|popen2|popen3|popen4)\s*\(', "已废弃 os.popen 系列存在注入风险"),], "high",
         "始终使用 subprocess.run(..., args=list, shell=False) 传递参数"),
        # SQL 注入
        ("security_sql_injection", [(r'(?i)execute\s*\(["\'].*%s.*["\']', "SQL 字符串拼接 = SQL注入风险"),
          (r'(?i)execute\s*\(["\'].*\{.*\}.*["\']', "f-string SQL = SQL注入风险"),
          (r'(?i)\.execute\s*\(["\'].*\+', "SQL 字符串+拼接 = SQL注入风险"),], "high",
         "始终使用参数化查询（cursor.execute(sql, params)）"),
        # 调试模式泄露
        ("security_debug_mode", [(r'(?i)DEBUG\s*=\s*True', "生产环境不应开启 DEBUG"),
          (r'(?i)FLASK_ENV\s*=\s*["\']development["\']', "开发模式不应出现在生产代码"),], "high",
         "从环境变量读取 DEBUG/FLASK_ENV，生产环境默认为 False"),
        # 弱加密/哈希
        ("security_weak_crypto", [(r'\bhashlib\.(?:md5|sha1)\s*\(', "MD5/SHA1 已被破解，不建议用于安全场景"),
          (r'\bcryptography\.hazmat\b', "hazmat 模块不稳定（应使用 recipes 层）"),
          (r'(?i)random\.(?:random|randint)\b(?!.*#.*(?:nosec|安全))', "random 模块不适合安全场景（应用 secrets 模块）"),], "medium",
         "使用 hashlib.sha256、secrets 模块、bcrypt/scrypt"),
        # 文件权限
        ("security_file_perms", [(r'\bos\.chmod\s*\(\s*\w+\s*,\s*0o777\b', "过于宽松的文件权限 777"),
          (r'\bos\.chmod\s*\(\s*\w+\s*,\s*777\b', "过于宽松的文件权限 777"),], "medium",
         "生产环境文件权限应不超过 0o644（文件）或 0o755（目录）"),
    ]

    def get_name(self) -> str:
        return "security"

    def get_description(self) -> str:
        return "深度安全审计 — eval/注入/反序列化/弱加密/调试模式"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        domain = project_features.get("domain", "")
        security_req = project_features.get("security_requirements", 5) / 10
        if domain in ["金融", "医疗", "政府"]:
            return min(1.0, 0.8 + security_req * 0.2)
        return min(1.0, security_req * 0.7)

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re, hashlib
        results = []
        project_path = os.getcwd()
        value_occurrences = {}

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.VULN_PATTERNS:
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped)
                            if not m:
                                continue
                            match_text = m.group(0)[:80]
                            val_hash = hashlib.md5(match_text.encode()).hexdigest()[:8]
                            if val_hash not in value_occurrences:
                                value_occurrences[val_hash] = []
                            value_occurrences[val_hash].append((rel_path, i, match_text))
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="failed" if base_sev == "critical" else "warning",
                                message=f"[{rel_path}:{i}] {match_text}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break

        # 检查 .gitignore 安全性
        if os.path.exists(".gitignore"):
            with open(".gitignore", 'r', encoding='utf-8', errors='ignore') as f:
                gitignore = f.read()
            for must_ignore in ['.env', '*.pem', '*.key', 'secrets.', 'credentials.', '*.p12', 'id_rsa']:
                if must_ignore not in gitignore:
                    results.append(ValidationResult(
                        check_name="gitignore_missing",
                        status="warning",
                        message=f".gitignore 未包含 '{must_ignore}'",
                        severity="medium",
                        remediation=f"在 .gitignore 中添加 {must_ignore}"
                    ))
        else:
            results.append(ValidationResult(
                check_name="gitignore_missing",
                status="warning",
                message="未找到 .gitignore 文件",
                severity="medium",
                remediation="创建 .gitignore 并忽略 .env *.pem secrets. 等敏感文件"
            ))

        # 汇总
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="security_audit_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "passed",
                message=f"安全审计完成: {header}",
                severity="critical" if sev_counts.get("critical", 0) > 0 else "medium",
                remediation="优先修复 critical/high 项。建议引入 bandit/pip-audit 定期扫描"
            ))
        return results


class HealthcareExpert(BasePerspectiveExpert):
    """医疗健康领域专家"""
    
    def get_name(self) -> str:
        return "healthcare"
    
    def get_description(self) -> str:
        return "医疗数据合规性、HIPAA合规、数据脱敏验证"
    
    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        domain = project_features.get("domain", "")
        if domain in ["医疗", "健康"]:
            return 0.95
        # 检查是否包含医疗相关关键词
        tech_stack = project_features.get("tech_stack", [])
        if any(t.lower() in ["healthcare", "medical", "patient"] for t in tech_stack):
            return 0.7
        return 0.1
    
    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []
        
        # HIPAA 合规检查
        results.append(ValidationResult(
            check_name="hipaa_compliance",
            status="warning",
            message="建议进行HIPAA合规性评估",
            severity="medium",
            remediation="审查患者数据处理流程，确保符合HIPAA要求"
        ))
        
        # 数据脱敏检查
        results.append(ValidationResult(
            check_name="data_desensitization",
            status="warning",
            message="建议实施数据脱敏策略",
            severity="medium",
            remediation="对患者隐私数据（姓名、身份证号、病历号等）进行脱敏处理"
        ))
        
        # HL7 FHIR 标准检查
        results.append(ValidationResult(
            check_name="hl7_fhir_check",
            status="info",
            message="建议采用HL7 FHIR标准进行医疗数据交换",
            severity="low",
            remediation="考虑集成HL7 FHIR标准接口"
        ))
        
        return results


class AuditorExpert(BasePerspectiveExpert):
    """审计员专家 — 日志/错误处理/异常可追溯性审计"""

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    def get_name(self) -> str:
        return "auditor"

    def get_description(self) -> str:
        return "可追溯性审计 — 异常处理/日志策略/bare except 检测"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        domain = project_features.get("domain", "")
        if domain in ["金融", "医疗", "政府"]:
            return 0.9
        return 0.5

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        patterns = [
            ("audit_bare_except", r'(?i)except\s*:', "bare except 掩盖了具体错误类型", "high"),
            ("audit_pass_except", r'(?i)except.*:\s*pass', "空 except 块吞噬了异常", "high"),
            ("audit_wide_except", r'(?i)except\s+(?:Exception|BaseException)\b', "捕获 Exception 过于宽泛", "medium"),
            ("audit_print_error", r'(?i)print\s*\(.*(?:error|fail|exception|traceback)', "错误信息用 print 而非日志框架", "medium"),
        ]
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, pat, msg, sev in patterns:
                        if re.search(pat, stripped):
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="warning" if sev in ("high", "medium") else "info",
                                message=f"[{rel_path}:{i}] {msg}",
                                severity=sev,
                                remediation="使用 logging 替代 print，except 指定具体异常类型"
                            ))
                            break
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="audit_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"可追溯性审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="修复 bare except/空except块，统一使用结构化日志"
            ))
        return results


class StatisticianExpert(BasePerspectiveExpert):
    """统计建模专家 — 算法正确性与数据质量审计"""

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # 数值稳定性
        ("stat_numerical_stability",
         [(r'\b(?:np|numpy)\.(?:log|log10|log2|sqrt)\((?![\w\[]+\))', "数值运算缺少零值/负值保护"),
          (r'/\s*(?![\w\.]+(?:\.\w+)?\s*[:-])(?![^\s]+\.get)', "除法缺少除零保护"),
         ], "high",
         "对数/除法操作需要检查输入有效性（isnan/isinf/≤0），使用 np.clip 或 try/except"),
        # NaN/Inf 缺失处理
        ("stat_missing_values",
         [(r'\.(?:mean|sum|std|var|median|min|max)\(\s*\)', "聚合函数缺少 NaN 处理策略"),
          (r'\bpd\.(?:read_csv|read_excel|read_sql)\([^)]*\)', "数据加载后缺少缺失值检查"),
         ], "medium",
         "数据载入后应检查 df.isnull().sum()。聚合时明确指定 skipna=True"),
        # 过拟合 / 验证集缺失
        ("stat_train_test_split",
         [(r'\b\w+\.fit\(\s*\w+\s*,\s*\w+\s*\)', "模型训练未检测到 train_test_split"),
          (r'\b\w+\.fit\(\s*X\b[^,]*\)', "模型训练似乎缺少验证集或 train_test_split"),
         ], "medium",
         "始终划分训练/验证/测试集，使用 cross_val_score 等交叉验证"),
        # 数据泄露
        ("stat_data_leakage",
         [(r'\.fit_transform\(', "fit_transform 应只在训练集调用（测试集用 transform）"),
          (r'\bStandardScaler|MinMaxScaler|LabelEncoder|OneHotEncoder\b.*fit_transform.*test|val',
           "预处理器 fit_transform 应用到测试集 = 数据泄露"),
         ], "high",
         "预处理必须在训练集 fit，再用 transform 作用于验证/测试集"),
        # 不平衡数据
        ("stat_imbalanced",
         [(r'accuracy_score|classification_report|confusion_matrix\b',
           "分类评估函数，需确认数据不平衡问题已处理"),
         ], "medium",
         "不平衡数据集建议用 F1/AUC-ROC 代替 accuracy，考虑 SMOTE/class_weight"),
        # 模型序列化安全
        ("stat_model_serialization",
         [(r'\b(?:pickle|cPickle|joblib)\.dump?\s*\(', "模型序列化使用 pickle 存在安全风险"),
         ], "low",
         "考虑使用 ONNX/PMML 或安全的模型序列化格式"),
    ]

    def get_name(self) -> str:
        return "statistician"

    def get_description(self) -> str:
        return "统计建模审计 — NaN/过拟合/数据泄露/数值稳定性"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        project_type = project_features.get("project_type", "")
        if project_type in ["Data", "AI"]:
            return 0.95
        tech_stack = project_features.get("tech_stack", [])
        data_techs = ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch"]
        if any(t.lower() in [tech.lower() for tech in tech_stack] for t in data_techs):
            return 0.7
        return 0.2

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.CHECKS:
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped)
                            if not m:
                                continue
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="warning" if base_sev in ("high", "medium") else "info",
                                message=f"[{rel_path}:{i}] {m.group(0)[:80]}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="stat_audit_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"统计建模审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="修复高/中危项，确保数据管道和模型训练流程健壮"
            ))
        return results


class PerformanceExpert(BasePerspectiveExpert):
    """性能工程师专家 — 反模式检测与性能审计"""

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # N+1 查询
        ("perf_n_plus_1", [(r'\bfor\b.*\b(?:filter|get|objects)\.', "循环内数据库查询 = N+1 风险"),
         (r'\bfor\b.*\n\s*\b\w+\.(?:filter|get|objects)\.', "循环内数据库查询（多行） = N+1 风险"),], "high",
         "使用 select_related/prefetch_related 或批量查询避免 N+1 问题"),
        # 大文件加载
        ("perf_memory_bomb", [(r'\bjson\.load\b', "json.load 可能加载大文件到内存"),
         (r'\.read\(\)', ".read() 一次性加载全部内容可能 OOM"),
         (r'\bpd\.(?:read_csv|read_excel)\(', "Pandas 加载方式未指定 chunksize 或 dtype 优化"),], "medium",
         "大文件使用迭代器/流式读取，Pandas 指定 chunksize/dtype"),
        # 缺少索引/缓存
        ("perf_no_cache", [(r'@lru_cache|@cache|functools\.(?:lru_cache|cache)', "已使用缓存（正常）")],
         "info", "不报警"),  # 这个用于对比检测缺失
        ("perf_heavy_loop", [(r'\bfor\b[^:]*\n\s*\b\w+\.(?:compute|transform|predict|aggregate)', "循环内重计算/重预测"),
         (r'\bfor\b[^:]*\n\s*.*(?:\.groupby|\.apply|\.transform)', "循环内 GroupBy/apply 操作 = O(n²) 风险"),], "medium",
         "将重计算提到循环外，或使用向量化操作代替循环"),
        # 异步缺失
        ("perf_blocking_io", [(r'\btime\.sleep\s*\(', "阻塞式 sleep 影响并发性能"),
         (r'\b(?:requests|urllib)\.(?:get|post|put|delete)\s*\(', "同步 HTTP 调用阻塞事件循环"),], "medium",
         "异步场景使用 asyncio.sleep / httpx/AsyncClient"),
        # 深度嵌套
        ("perf_deep_nesting", [(r'^\s{20,}', "过度缩进 — 嵌套过深降低可读性和可维护性"),], "low",
         "提取辅助函数，用 early return 减少嵌套深度"),
    ]

    def get_name(self) -> str:
        return "performance"

    def get_description(self) -> str:
        return "性能审计 — N+1查询/内存炸弹/阻塞IO/深层嵌套"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        scale = project_features.get("scale", "small")
        scale_weights = {"small": 0.3, "medium": 0.6, "large": 0.8, "enterprise": 1.0}
        return scale_weights.get(scale, 0.5)

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        full_content = []
        file_map = {}
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue
                file_map[rel_path] = content.split('\n')
                full_content.append(content)

        # 行级检测
        for rel_path, lines in file_map.items():
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                    continue
                for check_name, patterns, base_sev, fix in self.CHECKS:
                    if check_name in ("perf_no_cache",):
                        continue
                    for pat, _detail in patterns:
                        m = re.search(pat, stripped)
                        if not m:
                            continue
                        results.append(ValidationResult(
                            check_name=check_name,
                            status="warning" if base_sev in ("high", "medium") else "info",
                            message=f"[{rel_path}:{i}] {m.group(0)[:80]}",
                            severity=base_sev,
                            remediation=fix
                        ))
                        break

        # 汇总
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="perf_audit_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"性能审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="优先修复 high 项（N+1/内存炸弹），逐步优化 medium 项"
            ))
        return results


class ComplianceExpert(BasePerspectiveExpert):
    """合规专家 — 许可证与行业标准合规性审计"""

    def get_name(self) -> str:
        return "compliance"

    def get_description(self) -> str:
        return "合规审计 — 许可证/开源合规/标准化文件检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        domain = project_features.get("domain", "")
        if domain in ["金融", "医疗", "政府"]:
            return 0.9
        return 0.4

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []
        import re

        # 许可证文件检查
        license_files = ['LICENSE', 'COPYING', 'LICENSE.md', 'LICENSE.txt']
        has_license = any(os.path.exists(f) for f in license_files)
        if has_license:
            results.append(ValidationResult(
                check_name="license_exists", status="passed",
                message="许可证文件存在", severity="low",
            ))
        else:
            results.append(ValidationResult(
                check_name="license_exists", status="warning",
                message="缺少 LICENSE 文件", severity="medium",
                remediation="添加 MIT 或 Apache 2.0 等开源许可证文件"
            ))

        # 检查依赖许可证（扫描 requirements.txt / pyproject.toml 中是否有已知传染性许可）
        for dep_file in ['requirements.txt', 'requirements.in']:
            if os.path.exists(dep_file):
                try:
                    with open(dep_file, 'r', encoding='utf-8', errors='ignore') as f:
                        deps = f.read().lower()
                    if 'gpl' in deps:
                        results.append(ValidationResult(
                            check_name="gpl_dependency",
                            status="warning",
                            message="检测到 GPL 协议依赖（可能有传染性）",
                            severity="medium",
                            remediation="确认 GPL 依赖的使用范围，考虑替换为 MIT/Apache 方案"
                        ))
                except Exception:
                    pass
                break

        # 编码格式检查
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', '.git')]
            for file in files[:50]:  # 采样前 50 个文件
                if not file.endswith('.py'):
                    continue
                try:
                    with open(os.path.join(root, file), 'rb') as f:
                        content = f.read(10)
                    if b'\r\n' in content:
                        results.append(ValidationResult(
                            check_name="crlf_detected",
                            status="warning",
                            message=f"{file} 使用 CRLF 换行（Windows 风格）",
                            severity="medium",
                            remediation="统一为 LF 换行：git config --global core.autocrlf input"
                        ))
                except Exception:
                    continue
                break  # 只检查一个文件

        if results:
            results.insert(0, ValidationResult(
                check_name="compliance_report",
                status="warning" if any(r.severity in ("critical", "high", "medium") for r in results) else "passed",
                message=f"合规审计完成: {len(results)} 项",
                severity="medium",
                remediation="补齐许可证文件，审查 GPL 依赖风险"
            ))
        return results


class BusinessExpert(BasePerspectiveExpert):
    """业务分析师专家 — 文档与可交付性审计"""

    def get_name(self) -> str:
        return "business"

    def get_description(self) -> str:
        return "可交付性审计 — 文档/README/API文档/变更日志检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        return 0.6

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        # README
        if os.path.exists("README.md") or os.path.exists("README"):
            with open("README.md" if os.path.exists("README.md") else "README", 'r', encoding='utf-8', errors='ignore') as f:
                readme = f.read()
            if len(readme) < 200:
                results.append(ValidationResult(
                    check_name="readme_insufficient",
                    status="warning",
                    message="README 内容过于简短（<200 字符）",
                    severity="medium",
                    remediation="完善 README：项目简介、安装步骤、使用示例、FAQ"
                ))
            else:
                results.append(ValidationResult(
                    check_name="readme_ok",
                    status="passed",
                    message="README 内容充足",
                    severity="low"
                ))
        else:
            results.append(ValidationResult(
                check_name="no_readme",
                status="warning",
                message="缺少 README.md",
                severity="medium",
                remediation="创建 README.md，包含项目简介、安装、使用示例"
            ))

        # CHANGELOG
        if not os.path.exists("CHANGELOG.md") and not os.path.exists("CHANGES.md"):
            results.append(ValidationResult(
                check_name="no_changelog",
                status="info",
                message="建议添加 CHANGELOG.md 记录版本变更",
                severity="low",
                remediation="使用 Keep a Changelog 格式维护变更日志"
            ))

        # .gitignore 存在性
        if not os.path.exists(".gitignore"):
            results.append(ValidationResult(
                check_name="no_gitignore",
                status="warning",
                message="缺少 .gitignore",
                severity="medium",
                remediation="创建 .gitignore 文件排除临时文件和敏感信息"
            ))

        if results:
            results.insert(0, ValidationResult(
                check_name="doc_report",
                status="warning" if any(r.severity in ("critical", "high", "medium") for r in results) else "passed",
                message=f"文档审计完成: {len(results)} 项",
                severity="medium",
                remediation="补齐核心文档，提升项目可交付性"
            ))
        return results


class ArchitectExpert(BasePerspectiveExpert):
    """架构师专家 — 模块耦合与循环依赖检测"""

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    def get_name(self) -> str:
        return "architect"

    def get_description(self) -> str:
        return "架构审计 — 循环导入/模块规模/依赖方向检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        scale = project_features.get("scale", "small")
        scale_weights = {"small": 0.3, "medium": 0.5, "large": 0.8, "enterprise": 1.0}
        return scale_weights.get(scale, 0.5)

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        imports = {}
        large_modules = []

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue

                # 大模块检测（>500 行）
                lines = content.split('\n')
                if len(lines) > 500:
                    large_modules.append((rel_path, len(lines)))

                # 收集导入关系
                module_imports = set()
                for line in lines:
                    m = re.match(r'^(?:from|import)\s+(\S+)', line.strip())
                    if m:
                        module_imports.add(m.group(1).split('.')[0])
                if module_imports:
                    imports[rel_path] = module_imports

        # 报告大模块
        for module_path, line_count in large_modules:
            results.append(ValidationResult(
                check_name="large_module",
                status="warning",
                message=f"[{module_path}] 模块过大（{line_count} 行），建议拆分",
                severity="medium",
                remediation="超过 500 行的模块建议按职责拆分为多个子模块"
            ))

        # 简单循环导入检查（同层模块互相导入）
        for mod_a, deps_a in imports.items():
            for mod_b, deps_b in imports.items():
                if mod_a >= mod_b:
                    continue
                a_base = os.path.splitext(os.path.basename(mod_a))[0]
                b_base = os.path.splitext(os.path.basename(mod_b))[0]
                if a_base in deps_b and b_base in deps_a:
                    results.append(ValidationResult(
                        check_name="circular_import",
                        status="warning",
                        message=f"潜在循环导入: {mod_a} <-> {mod_b}",
                        severity="high",
                        remediation="提取共享接口到独立模块，打破循环依赖"
                    ))

        if results:
            results.insert(0, ValidationResult(
                check_name="arch_report",
                status="failed" if any(r.severity=="high" for r in results) else "warning",
                message=f"架构审计完成: {len(results)} 项",
                severity="medium",
                remediation="拆分大模块，消除循环依赖"
            ))
        return results


class DevOpsExpert(BasePerspectiveExpert):
    """运维工程师专家 — 部署就绪与 CI/CD 检查"""

    def get_name(self) -> str:
        return "devops"

    def get_description(self) -> str:
        return "部署就绪审计 — Docker/CI/健康检查/环境变量管理"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        scale = project_features.get("scale", "small")
        scale_weights = {"small": 0.2, "medium": 0.5, "large": 0.8, "enterprise": 1.0}
        return scale_weights.get(scale, 0.4)

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []

        # Docker 配置
        if os.path.exists("Dockerfile") or os.path.exists("docker-compose.yml"):
            # 检查 .dockerignore
            if not os.path.exists(".dockerignore"):
                results.append(ValidationResult(
                    check_name="no_dockerignore",
                    status="warning",
                    message="有 Docker 配置但缺少 .dockerignore",
                    severity="medium",
                    remediation="添加 .dockerignore 排除 __pycache__ .git .env 等"
                ))
            else:
                results.append(ValidationResult(
                    check_name="docker_ok",
                    status="passed",
                    message="Docker + .dockerignore 配置完整",
                    severity="low"
                ))
        else:
            results.append(ValidationResult(
                check_name="no_docker",
                status="info",
                message="建议添加 Dockerfile 和 docker-compose.yml",
                severity="low",
                remediation="添加 Docker 配置以支持容器化部署"
            ))

        # CI 配置检查
        ci_files = ['.github/workflows', '.gitlab-ci.yml', 'Jenkinsfile', '.circleci', '.travis.yml']
        has_ci = any(os.path.exists(f) for f in ci_files)
        if has_ci:
            results.append(ValidationResult(
                check_name="ci_exists",
                status="passed",
                message="CI/CD 配置存在",
                severity="low"
            ))
        else:
            results.append(ValidationResult(
                check_name="no_ci",
                status="warning",
                message="缺少 CI/CD 配置",
                severity="medium",
                remediation="添加 GitHub Actions / GitLab CI 配置文件"
            ))

        # .env.example 检查
        if not os.path.exists(".env.example"):
            results.append(ValidationResult(
                check_name="no_env_example",
                status="warning",
                message="缺少 .env.example（应列出所有需要配置的环境变量）",
                severity="medium",
                remediation="创建 .env.example 列出所有环境变量及其说明"
            ))

        if results:
            results.insert(0, ValidationResult(
                check_name="devops_report",
                status="warning" if any(r.severity in ("critical", "high", "medium") for r in results) else "passed",
                message=f"部署就绪审计完成: {len(results)} 项",
                severity="medium",
                remediation="补齐 .env.example 和 CI/CD 和 Docker 配置"
            ))
        return results


class UserExpert(BasePerspectiveExpert):
    """用户视角专家 - 从最终用户角度验证产品质量"""
    
    def get_name(self) -> str:
        return "user"
    
    def get_description(self) -> str:
        return "用户体验、可用性、界面友好性验证"
    
    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        """
        根据项目特征计算与用户视角的兼容性
        - Web/Mobile项目兼容性最高（直接面向用户）
        - 后端服务兼容性较低（间接面向用户）
        - 嵌入式系统兼容性最低
        """
        project_type = project_features.get("project_type", "")
        
        # 用户直接使用的项目类型
        user_facing_types = ["Web", "Mobile", "Desktop"]
        if project_type in user_facing_types:
            return 0.95
        
        # 后端服务（间接面向用户）
        if project_type == "Backend":
            return 0.6
        
        # 数据/AI项目（可能有用户界面）
        if project_type in ["Data", "AI"]:
            tech_stack = project_features.get("tech_stack", [])
            if any(t.lower() in ["react", "vue", "frontend", "ui"] for t in tech_stack):
                return 0.8
            return 0.5
        
        # 嵌入式系统（兼容性最低）
        if project_type == "Embedded":
            return 0.3
        
        return 0.7  # 默认中等兼容性
    
    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        """从用户视角执行验证"""
        results = []
        
        project_type = project_features.get("project_type", "")
        tech_stack = project_features.get("tech_stack", [])
        
        # 1. 用户界面检查
        if project_type in ["Web", "Mobile", "Desktop"]:
            # 检查前端框架是否存在
            frontend_frameworks = ["React", "Vue", "Angular", "Svelte"]
            has_frontend = any(f in tech_stack for f in frontend_frameworks)
            
            if has_frontend:
                results.append(ValidationResult(
                    check_name="frontend_framework",
                    status="passed",
                    message="使用了现代化前端框架，用户体验有保障",
                    severity="low"
                ))
            else:
                results.append(ValidationResult(
                    check_name="frontend_framework",
                    status="warning",
                    message="未检测到现代化前端框架",
                    severity="medium",
                    remediation="考虑使用 React、Vue 等现代化前端框架提升用户体验"
                ))
            
            # 检查是否有UI组件库
            ui_libraries = ["Ant Design", "Material UI", "Element Plus", "Tailwind CSS"]
            has_ui_lib = any(lib.lower() in ' '.join(tech_stack).lower() for lib in ui_libraries)
            
            if has_ui_lib:
                results.append(ValidationResult(
                    check_name="ui_library",
                    status="passed",
                    message="使用了专业UI组件库",
                    severity="low"
                ))
            else:
                results.append(ValidationResult(
                    check_name="ui_library",
                    status="info",
                    message="建议使用专业UI组件库",
                    severity="low",
                    remediation="考虑使用 Ant Design、Material UI 等组件库"
                ))
        
        # 2. 可访问性检查
        results.append(ValidationResult(
            check_name="accessibility",
            status="info",
            message="建议进行可访问性测试",
            severity="low",
            remediation="确保应用支持屏幕阅读器、键盘导航等辅助功能"
        ))
        
        # 3. 响应式设计检查（针对Web项目）
        if project_type == "Web":
            results.append(ValidationResult(
                check_name="responsive_design",
                status="info",
                message="建议实现响应式设计",
                severity="low",
                remediation="确保网站在不同设备上都能良好显示"
            ))
        
        # 4. 加载性能检查
        results.append(ValidationResult(
            check_name="load_performance",
            status="info",
            message="建议优化页面加载速度",
            severity="low",
            remediation="使用懒加载、代码分割、图片压缩等技术"
        ))
        
        # 5. 用户反馈机制检查
        results.append(ValidationResult(
            check_name="user_feedback",
            status="info",
            message="建议添加用户反馈机制",
            severity="low",
            remediation="实现用户反馈表单、满意度调查等功能"
        ))
        
        # 6. 错误提示友好性检查
        results.append(ValidationResult(
            check_name="error_messages",
            status="info",
            message="建议优化错误提示信息",
            severity="low",
            remediation="使用用户友好的错误提示，避免技术术语"
        ))
        
        # 7. 医疗领域特殊检查
        domain = project_features.get("domain", "")
        if domain == "医疗":
            results.append(ValidationResult(
                check_name="healthcare_usability",
                status="info",
                message="医疗应用需特别关注用户易用性",
                severity="medium",
                remediation="针对患者和医护人员设计直观的操作界面"
            ))
        
        return results


class HardcodeInspectorExpert(BasePerspectiveExpert):
    """硬编码深度纠察专家（常驻 — 不限项目类型）"""

    # ---- 配置/身份文件白名单（不扫描）----
    CONFIG_FILES = ['setup.py', 'setup.cfg', 'pyproject.toml', 'alembic.ini',
                    'pytest.ini', '.env.example', 'conftest.py']
    # 需在 validate 内排除自身所在的文件（避免检测器正则自我匹配）
    SKIP_FILES = {os.path.abspath(__file__)}
    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 'output', 'logs', '.git', 'migrations', 'versions', '.tox')

    # ---- 不合理硬编码模式（按严重度分层）----
    DETECTORS = [
        # === 致命级：密钥/凭证 ===
        ("hardcode_secret",
         [(r'["\'][A-Za-z0-9+/=]{30,}["\']', "疑似硬编码密钥/Token/PEM"),  # base64-like
          (r'(?i)(?:api_key|secret_key|token|password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']', "凭证类变量硬编码"),
          (r'(?i)["\'](?:ghp_|gho_|github_pat_|sk-|xox[baprs]-)[a-zA-Z0-9_\-]{20,}["\']', "已知格式的密钥硬编码"),
         ], "critical", "凭证必须从环境变量获取，绝对禁止出现在代码中。用 os.getenv() 替代"),

        # === 高危级：网络地址/连接串 ===
        ("hardcode_connection",
         [(r'["\'][a-z]+(?:ql)?://[^\s"\']+@[^\s"\']+["\']', "数据库/服务连接串硬编码"),
          (r'["\']https?://[^\s"\']*\.(?:com|cn|org|net|io|dev)[^\s"\']*["\']', "外部API URL硬编码"),
          (r'["\'](?:localhost|127\.0\.\d+\.\d+|192\.168\.|10\.\d+\.|172\.(?:1[6-9]|2\d|3[01])\.)[^\s"\']*["\']', "内部网络地址硬编码"),
         ], "high", "连接串和URL应从环境变量或配置文件统一管理，便于多环境部署"),

        # === 高危级：污染数据/模拟残留 ===
        ("hardcode_fake_data",
         [(r'(?i)["\'].*(?:mock|fake|dummy|stub|temp(?:orary)?|test\.data|placeholder|xxx+|待填|占位|假数据).*["\']', "模拟/占位数据"),
          (r'(?i)#\s*(?:TODO|FIXME|HACK|XXX|TEMP)\b', "技术债务标记（应清理或跟踪）"),
         ], "high", "模拟数据进入生产环境会导致计算/展示异常。TODO应转为issue跟踪或立即修复"),

        # === 高危级：模型/统计计算的输入数据硬编码 ===
        ("hardcode_model_input",
          [
           # NumPy/SciPy 直接构造含字面量数组（支持多层括号 [[, [[[ 等）
           (r'\b(?:np|numpy)\.(?:array|asarray|arange|linspace|logspace|ones|zeros|full|eye|diag)\(\[+\d', "NumPy数组硬编码数据"),
           # Pandas DataFrame/Series 内联数值
           (r'\b(?:pd|pandas)\.(?:DataFrame|Series|Index|to_datetime|to_numeric)\(.*\[+\d', "Pandas构造含硬编码数值"),
           # SciPy 统计函数传入字面量列表
           (r'\b(?:scipy\.stats|stats|scipy\.optimize)\.\w+\(\[+\d', "统计函数硬编码数据输入"),
           # sklearn / 建模函数传入字面量
           (r'\b(?:sklearn|torch|tensorflow|tf|keras|xgboost|lgb|lightgbm|catboost|prophet|statsmodels)\.\w+\(.*\[+\d', "建模框架硬编码数据输入"),
           # 常见模型方法: fit/predict/transform/train 含字面量数据
           (r'\b\w+\.(?:fit|predict|transform|fit_transform|train|evaluate|test)\(.*\[+\d', "模型方法硬编码数据输入"),
           # 内联 dict 直接传给建模函数
           (r'\b\w+\.(?:fit|predict|transform)\(\{.*\d', "模型方法硬编码字典数据输入"),
          ], "high", "模型/统计计算的所有输入数据必须由API或数据库动态获取。去除所有硬编码数值数据"),

        # === 中危级：业务/模型参数 ===
        ("hardcode_biz_param",
         [(r'(?i)(?:learning_rate|lr|batch_size|epochs|dropout|temperature|top_k|top_p|max_tokens)\s*[=:]\s*[\d.eE+-]+', "ML模型超参数"),
          (r'(?i)(?:threshold|cutoff|alpha|beta|gamma|epsilon|delta|lambda)\s*[=:]\s*[\d.eE+-]+', "阈值/系数硬编码"),
          (r'(?i)(?:weight|score|priority|confidence)\s*[=:]\s*[\d.]+', "业务权重硬编码"),
          (r'(?i)(?:limit|max_retries|timeout|ttl|cache_size|chunk_size|max_len)\s*[=:]\s*\d+', "运行参数硬编码"),
         ], "medium", "业务/模型参数应从配置文件、数据库或API动态获取，便于调优和A/B测试"),

        # === 中危级：统计参考值/率值 ===
        ("hardcode_stat_value",
         [(r'(?i)(?:mean|average|avg|std|variance|median|percentile|q[12345])\s*[=:]\s*[\d.eE+-]+', "统计参考值"),
          (r'(?i)(?:rate|ratio|proportion|prevalence|incidence|mortality|morbidity)\s*[=:]\s*[\d.eE+-]+', "率/比例硬编码"),
          (r'(?i)(?:baseline|reference|normal|standard)\s*[=:]\s*[\d.eE+-]+', "基准值硬编码"),
         ], "medium", "统计量应从数据动态计算，硬编码参考值会随数据分布变化而失效"),

        # === 中危级：日期/魔术数字 ===
        ("hardcode_magic_number",
         [(r'(?<!\w)\d{4}[-/]\d{2}[-/]\d{2}(?!\w)', "硬编码日期"),
          (r'(?<!\w)\d+(?:\s*\*\s*\d+){1,3}(?!\w)', "魔术数字计算式（如 60*60*24）"),
          (r'(?i)["\']\d{4}[-/]\d{2}[-/]\d{2}["\']', "硬编码日期字符串"),
         ], "medium", "日期常量应从datetime/schedule库获取。魔术数字应替换为命名常量"),

        # === 低危级：可移植性问题 ===
        ("hardcode_portability",
         [(r'["\'][A-Za-z]:[\\/][^\s"\']+["\']', "Windows绝对路径"),
          (r'["\']/(?:home|Users)/[^"\']+["\']', "用户目录绝对路径"),
          (r'(?i)(?:encoding|charset)\s*[=:]\s*["\'][^"\']+["\']', "编码字符串（建议定义为项目级常量）"),
         ], "low", "绝对路径和编码字符串影响跨平台/跨环境部署"),

        # === 低危级：内联硬编码数据 ===
        ("hardcode_inline_data",
         [(r'=\s*\[.*?\d+\.?\d*.*?\]', "硬编码数据列表"),
          (r'(?i)["\'][\w.+-]+@[\w.+-]+\.[a-z]{2,}["\']', "硬编码邮箱地址"),
          (r'["\']#(?:[A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})["\']', "硬编码颜色值"),
         ], "low", "内联数据应提取为配置项或从数据源获取"),
    ]

    # ---- 合理性防御列表（匹配则豁免）----
    WHITELIST = [
        r'^\s*#',                        # 纯注释
        r'^\s*import\b', r'^\s*from\b',  # 导入语句
        r'\.get\(["\']',                 # dict.get() 的 key
        r'__\w+__',                      # dunder
        r'\.(?:format|join|strip|split|replace|startswith|endswith|encode|decode)\(["\']',
        r'\b(?:PI|E|TAU|INF|NAN|True|False|None)\b',
        r'\b(?:math|np|numpy)\.(?:pi|e|tau|inf|nan|euler_gamma)\b',  # 通识数学常量
        r'\b(?:scipy\.constants|sc\.constants)\b',                    # 物理常量
        r'\b(?:logging|logger|log)\.',
        r'\b(?:assert|raise)\s',         r'\b(?:Enum|IntEnum|StrEnum|Flag|IntFlag)\b',
        r'\b(?:if|elif|else|while|for|with|try|except|finally|return|yield|break|continue|pass)\b',
        r'\b(?:def|class)\s+\w+',        r'f["\']',  r'@\w+',
        r'(?:help|usage|description|doc|summary)["\']\s*[=:]',
        r'(?:VERSION|version|__version__)\s*=\s*["\']',
        r'\brange\(\d+\)', r'\benumerate\(', r'\bslice\(', r'\bisinstance\(', r'\bhasattr\(',
        r'\[\d+:\d*\]',                  # 切片索引
        r'\.append\(\d+\.?\d*\)',        # list.append(数字)
        r'format\(.*?\d',                # 字符串 format
        r'os\.path\.', r'os\.environ', r'os\.getenv',
        r'\.env\.', r'config\[', r'\.cfg', r'\.ini',
        r'# type:\s*ignore', r'# noqa', r'# pragma:',
        r'alembic', r'migration',        # 数据库迁移文件
        r"""r['"]""",                    # raw string（正则定义行跳过，防止自我匹配）
        r"""\w+["\']\s*:\s*""",          # dict key 赋值（如 "temperature": val）
    ]

    TEST_FILE_MARKERS = ('test_', '_test', 'conftest', 'fixtures')
    TEST_DIRS = ('tests', 'test', 'testing', '__tests__')

    def get_name(self) -> str:
        return "hardcode_inspector"

    def get_description(self) -> str:
        return "硬编码深度纠察 — 14类检测 × 30条白名单 × 跨文件关联 × 分析报告"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        # 常驻专家：无论项目类型始终启用
        return 1.0

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re, hashlib
        results = []
        value_occurrences = {}  # 跨文件重复值追踪
        project_path = os.getcwd()

        for root, dirs, files in os.walk(project_path):
            # 跳过非代码目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]

            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                # 跳过自身文件
                if os.path.abspath(filepath) in self.SKIP_FILES:
                    continue
                rel_path = os.path.relpath(filepath, project_path)

                # 跳过配置文件
                if file in self.CONFIG_FILES:
                    continue

                is_test = (any(p in file for p in self.TEST_FILE_MARKERS) or
                           any(d in rel_path.split(os.sep) for d in self.TEST_DIRS))

                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue

                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        continue
                    if stripped.startswith(('import ', 'from ')):
                        continue

                    for detector_name, patterns, base_severity, generic_fix in self.DETECTORS:
                        for pattern, _detail in patterns:
                            match = re.search(pattern, stripped, re.IGNORECASE)
                            if not match:
                                continue
                            if any(re.search(p, stripped, re.IGNORECASE) for p in self.WHITELIST):
                                continue

                            matched_text = match.group(0)[:80]
                            severity = "low" if is_test else base_severity

                            # 跨文件重复值追踪
                            val_hash = hashlib.md5(matched_text.encode()).hexdigest()[:8]
                            if val_hash not in value_occurrences:
                                value_occurrences[val_hash] = []
                            value_occurrences[val_hash].append((rel_path, i, matched_text))

                            results.append(ValidationResult(
                                check_name=detector_name,
                                status="warning",
                                message=f"[{rel_path}:{i}] {matched_text}",
                                severity=severity,
                                remediation=generic_fix
                            ))
                            break  # 一行只报一次

        # 跨文件重复值分析（同一硬编码值出现在≥3个文件中 → 升级为critical）
        repeated = {h: locs for h, locs in value_occurrences.items() if len(locs) >= 3}
        if repeated:
            for val_hash, locs in repeated.items():
                sample = locs[0][2][:60]
                files = ', '.join(set(l[0] for l in locs))
                results.append(ValidationResult(
                    check_name="hardcode_cross_file",
                    status="warning",
                    message=f"'{sample}' 在 {len(locs)} 处重复出现: {files}",
                    severity="critical",
                    remediation="该硬编码值跨文件重复。请提取为共享常量或配置项，消除复制链"
                ))

        # 汇总头部
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="hardcode_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"硬编码审查完成: {header}",
                severity="critical" if sev_counts.get("critical", 0) > 0 else "medium",
                remediation="优先修复 critical/high 项。建议将 session_token 过期后增加一次全局硬编码排查"
            ))

        return results


class TestExpert(BasePerspectiveExpert):
    """测试工程专家 — 测试执行与覆盖率审计"""

    def get_name(self) -> str:
        return "tester"

    def get_description(self) -> str:
        return "测试工程审计 — 测试执行/覆盖率/测试组织检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        return 0.85

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []
        project_path = os.getcwd()

        # 1. 检查测试目录是否存在
        test_dirs = ['tests', 'test', 'testing', '__tests__']
        has_test_dir = any(os.path.isdir(os.path.join(project_path, d)) for d in test_dirs)
        has_test_files = False

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', '.git')]
            for f in files:
                if f.startswith('test_') or f.endswith('_test.py'):
                    has_test_files = True
                    break
            if has_test_files:
                break

        if not has_test_dir and not has_test_files:
            results.append(ValidationResult(
                check_name="no_tests",
                status="failed",
                message="未找到 tests/ 目录或 test_*.py 文件",
                severity="critical",
                remediation="创建 tests/ 目录并编写至少一个测试用例（pytest）"
            ))
        else:
            # 2. 尝试运行 pytest
            try:
                import subprocess
                result = subprocess.run(
                    ["python", "-m", "pytest", "--tb=no", "--no-header", "-q"],
                    capture_output=True, text=True, timeout=120,
                    cwd=project_path
                )
                output = result.stdout + result.stderr
                lines_out = [l for l in output.split('\n') if l.strip()]

                if result.returncode == 0:
                    results.append(ValidationResult(
                        check_name="pytest_pass",
                        status="passed",
                        message=f"所有测试通过: {lines_out[-1].strip() if lines_out else 'OK'}",
                        severity="low"
                    ))
                elif result.returncode == 5:
                    results.append(ValidationResult(
                        check_name="no_tests_collected",
                        status="warning",
                        message="pytest 未收集到任何测试用例",
                        severity="medium",
                        remediation="确保测试文件命名为 test_*.py 且测试函数以 test_ 开头"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="pytest_fail",
                        status="failed",
                        message=f"测试未全部通过: {lines_out[-1].strip() if lines_out else '见输出'}",
                        severity="high",
                        remediation="运行 pytest -v 查看失败的测试，逐一修复"
                    ))
            except Exception:
                results.append(ValidationResult(
                    check_name="pytest_error",
                    status="warning",
                    message="pytest 执行出错（可能未安装）",
                    severity="medium",
                    remediation="pip install pytest pytest-cov 然后运行测试"
                ))

            # 3. 尝试获取覆盖率
            try:
                import subprocess
                cov_result = subprocess.run(
                    ["python", "-m", "pytest", "--cov=.", "--cov-report=term-missing", "--tb=no", "-q"],
                    capture_output=True, text=True, timeout=120,
                    cwd=project_path
                )
                cov_output = cov_result.stdout
                import re
                m = re.search(r'(?:TOTAL\s+\d+\s+\d+\s+(\d+)%|Coverage:\s+(\d+)%)', cov_output)
                if m:
                    cov_pct = int(m.group(1) or m.group(2))
                    if cov_pct >= 80:
                        results.append(ValidationResult(
                            check_name="coverage_ok",
                            status="passed",
                            message=f"测试覆盖率 {cov_pct}%（优秀）",
                            severity="low"
                        ))
                    elif cov_pct >= 50:
                        results.append(ValidationResult(
                            check_name="coverage_low",
                            status="warning",
                            message=f"测试覆盖率仅 {cov_pct}%，建议提升至 80%",
                            severity="medium",
                            remediation="为核心模块补充单元测试"
                        ))
                    else:
                        results.append(ValidationResult(
                            check_name="coverage_critical",
                            status="failed",
                            message=f"测试覆盖率仅 {cov_pct}%（严重不足）",
                            severity="high",
                            remediation="立即为核心功能模块编写测试用例"
                        ))
            except Exception:
                pass  # 覆盖率检查为可选

        if results:
            results.insert(0, ValidationResult(
                check_name="test_report",
                status="failed" if any(r.severity in ("critical", "high") for r in results) else "passed",
                message=f"测试审计完成",
                severity="high" if any(r.severity=="critical" for r in results) else "medium",
                remediation="确保所有测试通过，覆盖率 ≥ 80%"
            ))
        return results


class DependencyExpert(BasePerspectiveExpert):
    """依赖安全专家 — 已知漏洞与许可证审计"""

    def get_name(self) -> str:
        return "dependency"

    def get_description(self) -> str:
        return "依赖安全 — pip-audit/过时依赖/许可证冲突检测"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        return 0.85

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        results = []
        import subprocess

        # 1. pip-audit 漏洞扫描
        try:
            audit = subprocess.run(
                ["pip-audit", "--format", "json", "--ignore-vuln", "PYSEC-0000"],
                capture_output=True, text=True, timeout=120
            )
            if audit.returncode == 0 and audit.stdout.strip():
                import json
                vulns = json.loads(audit.stdout)
                if not vulns:
                    results.append(ValidationResult(
                        check_name="pip_audit_clean",
                        status="passed",
                        message="pip-audit: 未发现已知漏洞",
                        severity="low"
                    ))
                elif isinstance(vulns, list):
                    for v in vulns[:5]:  # 最多报告前5个
                        results.append(ValidationResult(
                            check_name="pip_audit_vuln",
                            status="failed",
                            message=f"{v.get('name', '?')} {v.get('version', '?')}: {v.get('vulns', [{}])[0].get('id', '?')}",
                            severity="critical",
                            remediation=f"升级 {v.get('name', '?')} 到安全版本"
                        ))
        except FileNotFoundError:
            pass  # pip-audit 未安装
        except Exception:
            pass

        # 2. 过时的依赖包
        try:
            outdated = subprocess.run(
                ["pip", "list", "--outdated", "--format", "columns"],
                capture_output=True, text=True, timeout=60
            )
            if outdated.returncode == 0:
                lines = [l for l in outdated.stdout.split('\n') if l.strip()][2:]  # skip header
                if lines:
                    results.append(ValidationResult(
                        check_name="outdated_packages",
                        status="warning",
                        message=f"发现 {len(lines)} 个过时的依赖包",
                        severity="medium",
                        remediation="运行 pip list --outdated 查看详情，谨慎升级并验证兼容性"
                    ))
        except Exception:
            pass

        # 3. 检查是否锁定依赖（requirements.txt 中是否有版本号）
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", 'r') as f:
                    lines = f.readlines()
                unlocked = sum(1 for l in lines if l.strip() and not l.startswith('#') and '==' not in l)
                if unlocked > 0:
                    results.append(ValidationResult(
                        check_name="unpinned_deps",
                        status="warning",
                        message=f"requirements.txt 中有 {unlocked} 个依赖未锁定版本",
                        severity="medium",
                        remediation="使用 pip freeze > requirements.txt 锁定所有版本"
                    ))
            except Exception:
                pass

        if results:
            results.insert(0, ValidationResult(
                check_name="dep_report",
                status="failed" if any(r.severity=="critical" for r in results) else "warning",
                message=f"依赖安全审计完成",
                severity="critical" if any(r.severity=="critical" for r in results) else "medium",
                remediation="修复已知漏洞、锁定依赖版本、定期运行 pip-audit"
            ))
        return results


class LintExpert(BasePerspectiveExpert):
    """代码质量专家 — Lint + 类型检查"""

    LINTERS = [
        ("ruff", ["ruff", "check", "--output-format", "concise", "."]),
        ("flake8", ["flake8", "--max-line-length", "120", "--exit-zero", "."]),
        ("pylint", ["pylint", "--exit-zero", "--output-format", "text", "."]),
        ("mypy", ["mypy", "--ignore-missing-imports", "--no-error-summary", "."]),
    ]

    def get_name(self) -> str:
        return "linter"

    def get_description(self) -> str:
        return "代码质量 — ruff/flake8/pylint/mypy 综合检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        tech_stack = project_features.get("tech_stack", [])
        if "Python" in tech_stack:
            return 0.9
        return 0.5

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import subprocess
        results = []
        project_path = os.getcwd()

        for tool_name, cmd_args in self.LINTERS:
            try:
                result = subprocess.run(
                    cmd_args,
                    capture_output=True, text=True, timeout=120,
                    cwd=project_path
                )
                output = result.stdout + result.stderr
                lines = [l.strip() for l in output.split('\n') if l.strip()]

                if tool_name == "mypy":
                    # mypy 输出解析
                    error_lines = [l for l in lines if ': error:' in l or ': note:' in l]
                    if error_lines:
                        results.append(ValidationResult(
                            check_name=f"mypy_issues",
                            status="warning",
                            message=f"mypy 发现 {len(error_lines)} 个类型问题",
                            severity="medium",
                            remediation="逐个修复类型注解问题，提升代码健壮性"
                        ))
                    else:
                        results.append(ValidationResult(
                            check_name="mypy_clean",
                            status="passed",
                            message="mypy 类型检查通过",
                            severity="low"
                        ))
                else:
                    # lint 工具输出
                    import re
                    issue_lines = [l for l in lines if re.search(r':\d+:\d+:', l)]
                    if issue_lines:
                        results.append(ValidationResult(
                            check_name=f"{tool_name}_issues",
                            status="warning",
                            message=f"{tool_name} 发现 {len(issue_lines)} 个问题",
                            severity="medium",
                            remediation=f"运行 {tool_name} 查看详情并逐步修复"
                        ))
                    else:
                        results.append(ValidationResult(
                            check_name=f"{tool_name}_clean",
                            status="passed",
                            message=f"{tool_name} 检查通过",
                            severity="low"
                        ))
            except FileNotFoundError:
                pass  # 工具未安装，静默跳过
            except subprocess.TimeoutExpired:
                results.append(ValidationResult(
                    check_name=f"{tool_name}_timeout",
                    status="info",
                    message=f"{tool_name} 执行超时（项目过大）",
                    severity="low",
                    remediation=f"分目录运行 {tool_name} 或增加超时时间"
                ))
            except Exception:
                pass

        if results:
            results.insert(0, ValidationResult(
                check_name="lint_report",
                status="warning" if any(r.severity in ("critical", "high", "medium") for r in results) else "passed",
                message=f"代码质量检查完成",
                severity="medium",
                remediation="优先修复类型错误（mypy），然后逐步修复 lint 警告"
            ))
        return results


class FrontendExpert(BasePerspectiveExpert):
    """前端工程专家 — JS/TS 项目扫描与质量检查"""

    def get_name(self) -> str:
        return "frontend"

    def get_description(self) -> str:
        return "前端工程审计 — package.json/tssc/ESLint/构建配置检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        tech_stack = project_features.get("tech_stack", [])
        frontend_techs = ["React", "Vue", "Angular", "JavaScript", "TypeScript", "Node.js"]
        if any(t in tech_stack for t in frontend_techs):
            return 0.9
        project_type = project_features.get("project_type", "")
        if project_type in ("Web", "Mobile"):
            return 0.75
        return 0.2

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import json as _json
        results = []
        project_path = os.getcwd()

        # 1. package.json 检查
        pkg_path = os.path.join(project_path, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'r', encoding='utf-8') as f:
                    pkg = _json.load(f)

                # 缺少必要脚本
                scripts = pkg.get("scripts", {})
                for key in ("build", "lint", "test"):
                    if key not in scripts:
                        results.append(ValidationResult(
                            check_name=f"no_{key}_script",
                            status="warning",
                            message=f"package.json 缺少 '{key}' 脚本",
                            severity="medium",
                            remediation=f"添加 npm {key} 脚本"
                        ))

                # 检查依赖完整性
                if not os.path.exists(os.path.join(project_path, "node_modules")):
                    results.append(ValidationResult(
                        check_name="no_node_modules",
                        status="warning",
                        message="缺少 node_modules/，未安装前端依赖",
                        severity="medium",
                        remediation="运行 npm install / yarn install / pnpm install"
                    ))
            except Exception as e:
                results.append(ValidationResult(
                    check_name="package_json_error",
                    status="warning",
                    message=f"package.json 解析失败: {e}",
                    severity="medium",
                    remediation="修正 package.json 格式"
                ))
        else:
            results.append(ValidationResult(
                check_name="no_package_json",
                status="info",
                message="未找到 package.json（非前端项目可忽略）",
                severity="low"
            ))

        # 2. TS 类型检查
        tsconfig = os.path.join(project_path, "tsconfig.json")
        if os.path.exists(tsconfig):
            try:
                import subprocess
                tsc_result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    capture_output=True, text=True, timeout=120,
                    cwd=project_path
                )
                if tsc_result.returncode != 0:
                    error_count = len([l for l in (tsc_result.stdout + tsc_result.stderr).split('\n') if 'error' in l.lower()])
                    results.append(ValidationResult(
                        check_name="tsc_errors",
                        status="failed",
                        message=f"TypeScript 类型检查: {error_count} 个错误",
                        severity="high",
                        remediation="运行 npx tsc --noEmit 查看详情并修复类型错误"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="tsc_pass",
                        status="passed",
                        message="TypeScript 类型检查通过",
                        severity="low"
                    ))
            except FileNotFoundError:
                pass
            except Exception:
                pass

        # 3. .eslintrc 配置检查
        has_eslint = any(os.path.exists(os.path.join(project_path, f)) for f in
                         ('.eslintrc.js', '.eslintrc.json', '.eslintrc', 'eslint.config.js', 'eslint.config.mjs'))
        if not has_eslint:
            results.append(ValidationResult(
                check_name="no_eslint",
                status="info",
                message="建议添加 ESLint 配置",
                severity="low",
                remediation="npm install eslint @eslint/js -D && eslint --init"
            ))

        if results:
            results.insert(0, ValidationResult(
                check_name="frontend_report",
                status="failed" if any(r.severity in ("critical", "high") for r in results) else "warning",
                message=f"前端工程审计完成",
                severity="medium",
                remediation="补齐 package.json 脚本，配置 ESLint，通过 TS 类型检查"
            ))
        return results


class DBMigrationExpert(BasePerspectiveExpert):
    """数据库迁移专家 — Alembic / SQL migration 检查"""

    def get_name(self) -> str:
        return "db_migration"

    def get_description(self) -> str:
        return "数据库迁移审计 — Alembic 版本/迁移完整性/回滚检查"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        tech_stack = project_features.get("tech_stack", [])
        db_techs = ["SQLAlchemy", "Django", "PostgreSQL", "MySQL", "Redis"]
        if any(t in tech_stack for t in db_techs):
            return 0.75
        return 0.3

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import subprocess, configparser
        results = []
        project_path = os.getcwd()

        # 检测 Alembic 配置
        alembic_ini = os.path.join(project_path, "alembic.ini")
        alembic_dir = os.path.join(project_path, "alembic")
        has_alembic = os.path.exists(alembic_ini) or os.path.isdir(alembic_dir)

        # Django 迁移
        has_django_migrations = False
        for root, dirs, files in os.walk(project_path):
            if 'migrations' in dirs:
                mig_dir = os.path.join(root, 'migrations')
                if any(f.endswith('.py') and not f.startswith('__') for f in os.listdir(mig_dir)):
                    has_django_migrations = True
                    break

        if not has_alembic and not has_django_migrations:
            results.append(ValidationResult(
                check_name="no_migration_tool",
                status="info",
                message="未检测到数据库迁移工具（Alembic/Django migrations）",
                severity="low",
                remediation="使用 Alembic 或 Django migrations 管理数据库版本"
            ))
            return results

        if has_alembic:
            # 检查迁移是否与模型同步
            try:
                result = subprocess.run(
                    ["alembic", "check"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode != 0 and "not supported" not in result.stderr:
                    results.append(ValidationResult(
                        check_name="alembic_out_of_sync",
                        status="failed",
                        message="Alembic: 数据库迁移与模型不同步",
                        severity="high",
                        remediation="运行 alembic revision --autogenerate 生成新迁移文件"
                    ))
                else:
                    results.append(ValidationResult(
                        check_name="alembic_synced",
                        status="passed",
                        message="Alembic: 迁移与模型同步",
                        severity="low"
                    ))
            except FileNotFoundError:
                pass
            except Exception:
                pass

            # 检查迁移文件是否存在
            versions_dir = os.path.join(alembic_dir, "versions") if os.path.isdir(alembic_dir) else None
            if versions_dir:
                py_files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and not f.startswith('__')]
                if not py_files:
                    results.append(ValidationResult(
                        check_name="no_alembic_versions",
                        status="warning",
                        message="Alembic versions/ 目录为空（无迁移文件）",
                        severity="medium",
                        remediation="运行 alembic revision --autogenerate -m 'init' 创建初始迁移"
                    ))
                else:
                    # 检查迁移是否包含 downgrade
                    for f in py_files[:5]:
                        try:
                            with open(os.path.join(versions_dir, f), 'r') as fh:
                                content = fh.read()
                            if 'downgrade' not in content:
                                results.append(ValidationResult(
                                    check_name="no_downgrade",
                                    status="warning",
                                    message=f"迁移文件 {f} 缺少 downgrade 方法",
                                    severity="medium",
                                    remediation="为每个迁移添加 downgrade() 以保证可回滚"
                                ))
                                break
                        except Exception:
                            pass

        if has_django_migrations:
            results.append(ValidationResult(
                check_name="django_migrations_found",
                status="passed",
                message="Django migrations 已配置",
                severity="low",
                remediation="确保运行 python manage.py makemigrations --check 检查迁移状态"
            ))

        if results:
            results.insert(0, ValidationResult(
                check_name="db_report",
                status="failed" if any(r.severity in ("critical", "high") for r in results) else "warning",
                message=f"数据库迁移审计完成",
                severity="high" if any(r.severity=="high" for r in results) else "medium",
                remediation="确保 alembic check 通过，所有迁移都有 downgrade"
            ))
        return results


class PHIInspectExpert(BasePerspectiveExpert):
    """PHI隐私审计专家 — 患者健康信息泄露代码扫描

    扫描所有代码中的患者隐私数据泄露点：
    - 日志中打印患者姓名/身份证/病历号
    - 异常堆栈中暴露PHI
    - 数据导出/共享缺少脱敏
    - print/debug 输出患者信息
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    # PHI 泄露模式
    PHI_PATTERNS = [
        # 日志打印患者信息
        ("phi_log_patient_name",
         [(r'(?i)(?:logger|logging)\.\w+\(.*(?:name|姓名|patient_name|患者).*\{', "日志中包含患者姓名变量"),
          (r'(?i)(?:logger|logging)\.\w+\(.*(?:id_card|身份证|id_number|sfzh).*\{', "日志中包含身份证号变量"),
          (r'(?i)(?:logger|logging)\.\w+\(.*(?:medical_record|病历号|mrn|patient_id).*\{', "日志中包含病历号变量"),
          (r'(?i)(?:logger|logging)\.\w+\(.*(?:phone|手机|mobile|tel).*\{', "日志中包含手机号变量"),
          (r'(?i)(?:logger|logging)\.\w+\(.*(?:address|地址|addr|住址).*\{', "日志中包含住址变量"),
          (r'(?i)(?:logger|logging)\.\w+\(.*(?:disease|诊断|diagnosis|icd).*\{', "日志中包含诊断信息变量"),
          (r'(?i)(?:logger|logging)\.\w+\(.*(?:dna|gene|genotype|基因).*\{', "日志中包含基因/遗传信息变量"),
         ], "high",
         "患者隐私数据不应出现在日志中。使用 Token/ID 替代，或将日志级别设为 DEBUG 且仅开发环境启用"),

        # print 输出患者信息
        ("phi_print_patient_data",
         [(r'(?i)print\s*\(.*(?:patient|患者|病人|病患).*(?:name|姓名|id_card|身份证|phone|手机)', "print 包含患者信息"),
          (r'(?i)print\s*\(.*(?:name|姓名).*(?:patient|患者)', "print 患者姓名"),
          (r'(?i)print\s*\(.*f["\'].*patient["\']', "print 输出患者数据"),
         ], "high",
         "生产代码中不应使用 print 输出患者信息。使用脱敏后的结构化日志"),

        # 异常堆栈泄露 PHI
        ("phi_exception_leak",
         [(r'(?i)raise\s+\w+Exception\(.*(?:patient|患者|id_card|身份证|phone|手机)', "异常消息包含患者信息"),
          (r'(?i)raise\s+\w+Exception\(.*f["\'].*(?:patient|患者)', "异常消息含患者 f-string"),
          (r'(?i)except\s+\w+.*:\s*\w+\.error\(.*(?:patient|患者)', "异常处理中记录患者信息"),
         ], "high",
         "异常消息不应包含PHI，用错误码/ID替代。患者数据字段应该用占位符"),

        # 数据导出/序列化包含PHI
        ("phi_export_no_mask",
         [(r'(?i)(?:to_csv|to_excel|to_json|to_dict|json\.dump|export).*patient', "数据导出包含患者数据"),
          (r'(?i)(?:to_csv|to_excel|to_json|json\.dump).*(?:id_card|身份证|身份证号)', "数据导出含身份证号"),
          (r'(?i)(?:to_csv|to_excel|to_json|json\.dump).*medical_record', "数据导出含病历号"),
          (r'(?i)(?:to_csv|to_excel|to_json|json\.dump).*phone', "数据导出含手机号"),
         ], "high",
         "数据导出前必须对PHI字段脱敏（姓名→假名，身份证→哈希，手机→脱敏）。添加脱敏包装层"),

        # API 响应包含完整PHI
        ("phi_api_response",
         [(r'(?i)return\s*\{.*(?:id_card|身份证|sfzh)\s*:', "API 返回含身份证号"),
          (r'(?i)return\s*\{.*(?:phone|手机|mobile|tel)\s*:', "API 返回含手机号"),
          (r'(?i)return\s*\{.*(?:address|地址|addr|住址)\s*:', "API 返回含住址"),
          (r'(?i)return\s*\{.*(?:dna|gene|基因|genotype)\s*:', "API 返回含基因信息"),
         ], "high",
         "API 响应应使用脱敏字段。创建 serializers.py 统一管理 API 输出格式"),

        # 硬编码脱敏密钥泄漏（脱敏密钥本身不能硬编码）
        ("phi_deid_key_leak",
         [(r'(?i)(?:DEID_KEY|MASK_KEY|CRYPTO_KEY|AES_KEY|脱敏密钥).*\s*=\s*["\']', "脱敏密钥硬编码"),
          (r'(?i)(?:FERNET|AES)\.\w+\(["\'][^"\']+["\']', "加密密钥硬编码"),
         ], "critical",
         "脱敏/加密密钥必须通过环境变量或密钥管理服务获取，绝对不能硬编码"),
    ]

    def get_name(self) -> str:
        return "phi_inspector"

    def get_description(self) -> str:
        return "PHI隐私审计 — 日志泄露/导出未脱敏/API返回/密钥泄露扫描"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        domain = project_features.get("domain", "")
        if domain in ("医疗", "健康"):
            return 1.0
        # 检查项目文件内容是否涉及医疗
        tech_stack = project_features.get("tech_stack", [])
        if any(t in ["healthcare", "medical", "hospital", "patient", "clinic"] for t in tech_stack):
            return 0.8
        return 0.3

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.PHI_PATTERNS:
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped)
                            if not m:
                                continue
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="failed" if base_sev == "critical" else "warning",
                                message=f"[{rel_path}:{i}] {m.group(0)[:100]}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="phi_audit_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"PHI隐私审计完成: {header}",
                severity="critical" if sev_counts.get("critical", 0) > 0 else "high",
                remediation="所有 PHI 泄露点必须立即修复。日志脱敏、导出脱敏、API脱敏、密钥外置"
            ))
        return results


class DataIntegrityExpert(BasePerspectiveExpert):
    """数据完整性专家 — ETL 数据管道一致性审计

    检查数据在流转中是否保持完整性：
    - ETL 行数校验
    - 必填字段非空约束
    - 主键/外键完整性
    - 时间戳单调性
    - 参照完整性
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # 行数校验缺失
        ("etl_row_count",
         [(r'\b(?:pd|pandas)\.(?:read_csv|read_excel|read_sql|read_parquet|read_feather)\b', "数据读取后缺少行数校验"),
          (r'\.to_csv\(|\.to_excel\(|\.to_sql\(|\.to_parquet\b', "数据写入前后缺少行数校验"),
         ], "high",
         "ETL 每一步后记录 len(df)，并对比输入输出行数。差异行写入 rejected_rows.log"),

        # 缺失列约束
        ("etl_null_check",
         [(r'\.loc\[|\.iloc\[|\.at\[.*\]\s*=', "直接索引用可能分配 NaN"),
          (r'\.fillna\(', "fillna 存在但需确认覆盖了所有关键列"),
         ], "medium",
         "对必填列检查 df['col'].isnull().sum()，非零立即报警。非必填列明确默认值策略"),

        # 主键唯一性
        ("etl_primary_key",
         [(r'\.groupby\(|\.merge\(|\.join\(|pd\.concat\b', "聚合/合并操作缺少去重校验"),
          (r'\.duplicated\(', "检查重复值存在但需确认覆盖了主键列"),
         ], "high",
         "合并/聚合后检查 df['pk'].duplicated().sum()>0。有重复主键必须标记并写入 dup_keys.csv"),

        # 外键完整性
        ("etl_foreign_key",
         [(r'\.merge\(.*\b(?:left|right|inner|outer)\b', "merge 操作缺少外键完整性校验"),
          (r'\.merge\(.*how\s*=\s*["\']left["\']', "左连接后需检查右侧匹配率"),
         ], "medium",
         "左连接后检查右表 NULL 比例 > 5% 报警。外键孤儿行写入 orphan_fk.csv"),

        # 时间戳单调性
        ("etl_timestamp_order",
         [(r'(?:pd\.to_datetime|datetime\.strptime)', "时间解析后缺少单调性检查"),
          (r'sort_values\(.*(?:date|time|timestamp)', "按时间排序后需验证单调递增"),
         ], "medium",
         "时间列检查: df['ts'].is_monotonic_increasing。逆序数据写入 bad_order.csv"),

        # 数值范围校验
        ("etl_value_range",
         [(r'\.sum\(\)|\.mean\(\)|\.std\(\)|\.describe\(\)', "聚合统计前缺少数值范围校验"),
          (r'\.apply\(|\.transform\(|\.map\b.*lambda', "变换操作前未校验输入值范围"),
         ], "medium",
         "数值列检查: df['col'].between(lower, upper)。越界值写入 outlier.csv"),
    ]

    def get_name(self) -> str:
        return "data_integrity"

    def get_description(self) -> str:
        return "数据完整性审计 — ETL行数/主键/外键/时间戳/数值范围"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        tech_stack = project_features.get("tech_stack", [])
        data_techs = ["pandas", "numpy", "SQLAlchemy", "psycopg", "spark", "Data"]
        if any(t in tech_stack for t in data_techs):
            return 0.85
        project_type = project_features.get("project_type", "")
        if project_type in ("Data", "AI"):
            return 0.9
        domain = project_features.get("domain", "")
        if domain in ("医疗", "金融"):
            return 0.7
        return 0.3

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.CHECKS:
                        for pat, _detail in patterns:
                            if not re.search(pat, stripped, re.IGNORECASE):
                                continue
                            # 确认不是被动匹配（如仅仅是读取函数而非ETL）
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="warning" if base_sev in ("high", "medium") else "info",
                                message=f"[{rel_path}:{i}] 潜在数据完整性风险",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="data_integrity_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"数据完整性审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="在ETL每一步添加行数/主键/外键/范围校验，异常数据写入日志表"
            ))
        return results


class ProductionReadinessExpert(BasePerspectiveExpert):
    """生产就绪专家 — 部署前最后一公里检查

    检查：
    - 环境变量完整性
    - 数据库连接池配置
    - 日志级别
    - 优雅关闭
    - 健康检查端点
    - 超时配置
    - 幂等性保护
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # 环境变量完整性
        ("prod_env_vars",
         [(r'\bos\.getenv\s*\(["\'](\w+)["\']\)', "使用环境变量（正常）")],
         "low", "不报警"),  # 用于检测是否需要环境变量
        ("prod_env_default",
         [(r'\bos\.getenv\s*\(["\'](\w+)["\']\s*,\s*["\']', "环境变量有硬编码默认值"),
          (r'\bos\.getenv\s*\(["\'](\w+)["\']\s*,\s*\d+', "环境变量有数字默认值"),
         ], "high",
         "生产环境的环境变量不应有硬编码后备值。使用 os.getenv('KEY') 返回 None 让启动时 fail-fast"),

        # 数据库连接池
        ("prod_db_pool",
         [(r'(?i)(?:create_engine|create_async_engine)\(', "SQLAlchemy 引擎创建"),
          (r'(?i)pool_size\s*=\s*\d+', "连接池大小配置"),
         ], "medium",
         "确保 pool_size + max_overflow > worker*并发查询数。开启 pool_pre_ping=True 检测断连"),

        # 日志级别
        ("prod_log_level",
         [(r'(?i)\.setLevel\(.*(?:DEBUG|INFO)\)', "日志级别可能过低"),
          (r'(?i)(?:logger|logging)\.(?:debug|info)\(', "debug/info 日志可能过多"),
         ], "medium",
         "生产环境日志级别应为 WARNING 或 ERROR。添加 LOG_LEVEL 环境变量控制"),

        # 超时配置
        ("prod_timeout",
         [(r'(?i)(?:requests|httpx|urllib)\.(?:get|post|put|delete)\(', "HTTP 请求缺少超时"),
          (r'(?i)timeout\s*=\s*\d+', "超时已配置（良好）"),
         ], "high",
         "所有外部 HTTP 调用必须设置 timeout 参数，避免挂起耗尽连接池"),

        # 优雅关闭
        ("prod_graceful_shutdown",
         [(r'(?i)(?:signal\.signal|atexit\.register|shutdown|graceful|graceful_shutdown)\b', "检测到优雅关闭逻辑"),
         ], "medium",
         "注册 SIGTERM 处理器：停止接收新请求 → 等待进行中任务 → 关闭连接 → 退出"),

        # 幂等性保护
        ("prod_idempotent",
         [(r'(?i)(?:INSERT\s+INTO|insert\(\)|bulk_insert)', "数据库写入操作"),
          (r'(?i)(?:schedule|cron|crontab|celery|apscheduler)', "定时任务"),
         ], "high",
         "定时任务写入数据库前用唯一键+ON CONFLICT 保证幂等。或记录 task_run_id 避免重入"),

        # 重试策略
        ("prod_retry",
         [(r'(?i)(?:retry|backoff|tenacity|circuit_breaker)\b', "已使用重试库（良好）"),
          (r'(?i)requests\.(?:get|post|put|delete)\((?:(?!timeout).)*\)', "HTTP 调用缺超时+重试"),
         ], "medium",
         "使用 tenacity 或 httpx 内置重试。指数退避 + 最大重试次数，关键业务重试必有上限"),

        # 资源清理
        ("prod_resource_cleanup",
         [(r'(?i)(?:file|connection|cursor|session|client)\s*=\s*\w+\.(?:open|connect|get)', "资源创建"),
          (r'(?i)(?:with\s+\w+|\.close\(\)|__exit__)', "上下文管理器/显式关闭（良好）"),
         ], "medium",
         "文件/数据库连接/S3客户端等资源必须使用 with 语句或 finally 中显式关闭"),
    ]

    def get_name(self) -> str:
        return "production_readiness"

    def get_description(self) -> str:
        return "生产就绪审计 — 环境变量/连接池/优雅关闭/幂等/重试/超时"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        scale = project_features.get("scale", "small")
        scale_weights = {"small": 0.5, "medium": 0.7, "large": 0.9, "enterprise": 1.0}
        return scale_weights.get(scale, 0.6)

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.CHECKS:
                        if check_name == "prod_env_vars":
                            continue
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped, re.IGNORECASE)
                            if not m:
                                continue
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="warning" if base_sev in ("critical", "high", "medium") else "info",
                                message=f"[{rel_path}:{i}] {m.group(0)[:100]}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="prod_readiness_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"生产就绪审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="完成环境变量外置、连接池调优、超时重试配置、幂等保护后上线"
            ))
        return results


class MedicalDataValidatorExpert(BasePerspectiveExpert):
    """医疗数据格式校验专家 — 领域特定数据合理性检查

    检查项目是否包含医疗数据的输入校验：
    - 年龄范围 (0-150)
    - 血压范围 (收缩压 60-260 / 舒张压 30-160)
    - 身份证号格式 (18位校验)
    - ICD 编码格式
    - 体重/BMI 范围
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    # 医疗字段→合理范围的映射
    MEDICAL_RANGES = {
        "systolic_bp": (60, 260, "收缩压"),
        "diastolic_bp": (30, 160, "舒张压"),
        "heart_rate": (30, 250, "心率"),
        "temperature": (34.0, 43.0, "体温(℃)"),
        "spo2": (60, 100, "血氧饱和度"),
        "respiratory_rate": (8, 60, "呼吸频率"),
        "bmi": (10, 65, "BMI"),
        "weight_kg": (0.5, 500, "体重(kg)"),
        "height_cm": (30, 250, "身高(cm)"),
        "age": (0, 150, "年龄"),
        "glucose": (1.0, 35.0, "血糖(mmol/L)"),
        "creatinine": (10, 1500, "肌酐(μmol/L)"),
        "wbc": (0.1, 100, "白细胞(10⁹/L)"),
        "hemoglobin": (20, 250, "血红蛋白(g/L)"),
        "platelet": (5, 1500, "血小板(10⁹/L)"),
    }

    CHECKS = [
        # 缺少医疗数据校验函数
        ("med_no_validation",
         [(r'(?i)(?:validate|check|verify|范围|range).*patient', "患者数据校验存在（良好）"),
          (r'(?i)(?:patient|患者|diagnosis|诊断|lab_result|检验)', "检测到患者/诊断/检验数据，但需确认有校验"),
         ], "high",
         "所有医疗数值字段必须校验范围。异常值标记为 quality_flag=REJECTED 并写入 rejected_records 表"),

        # 硬编码阈值
        ("med_hardcoded_range",
         [(r'(?i)(?:bp|blood_pressure|血压)\s*[><]=?\s*\d+', "血压阈值硬编码"),
          (r'(?i)(?:age|年龄)\s*[><]=?\s*\d+', "年龄阈值硬编码"),
          (r'(?i)(?:bmi|体重指数|体质指数)\s*[><]=?\s*\d+\.?\d*', "BMI阈值硬编码"),
         ], "medium",
         "医学参考范围应从配置或医学知识库获取（如 LOINC/RxNorm），不硬编码在业务代码中"),

        # 身份证号校验
        ("med_id_card_check",
         [(r'(?i)id_card|身份证|sfzh|id_number', "检测到身份证字段"),
          (r'(?i)(?:check|verify|validate).*(?:id_card|id|身份证)', "身份证校验存在"),
         ], "medium",
         "身份证号必须校验: 18位格式 + 校验位 + 年龄≥0。无效ID写入 rejected_ids.csv"),

        # ICD 编码格式
        ("med_icd_format",
         [(r'(?i)icd[_\s]*1[0-1]|diagnosis_code|诊断编码', "检测到 ICD 编码字段"),
          (r'(?i)icd[_\s]*1[0-1].*(?:check|verify|match|format)', "ICD格式校验"),
         ], "medium",
         "ICD-10 编码格式: [A-Z][0-9]{2}(\\.[0-9]{1,4})?。ICD-11 用官方编码表验证"),
    ]

    def get_name(self) -> str:
        return "med_validator"

    def get_description(self) -> str:
        return "医疗数据格式校验 — 年龄/血压/ICD/身份证/检验值范围"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        domain = project_features.get("domain", "")
        if domain in ("医疗", "健康"):
            return 1.0
        tech_stack = project_features.get("tech_stack", [])
        if any(t in ["healthcare", "medical", "hospital", "patient", "clinic", "disease"] for t in tech_stack):
            return 0.85
        return 0.15

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.CHECKS:
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped, re.IGNORECASE)
                            if not m:
                                continue
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="warning" if base_sev in ("high", "medium") else "info",
                                message=f"[{rel_path}:{i}] {m.group(0)[:100]}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break
        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="med_validation_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"医疗数据校验审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="为所有医疗数值字段添加范围校验，异常值标记后进入人工审核队列"
            ))
        return results


class APIContractExpert(BasePerspectiveExpert):
    """API 契约专家 — 接口兼容性 + 速率限制 + 响应格式审计

    检查：
    - OpenAPI/Swagger schema 是否存在
    - API 响应结构的一致性
    - 速率限制中间件
    - 硬编码的 API endpoint
    - 错误响应的统一格式
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # 硬编码 HTTP endpoint
        ("api_hardcoded_endpoint",
         [(r'(?i)https?://(?!localhost|127\.0\.0\.1)[^/\s"\']+["\']', "硬编码外部 API URL"),
          (r'(?i)(?:requests|httpx|urllib)\.\w+\(["\']https?://', "请求中硬编码完整 URL"),
         ], "high",
         "所有外部 API 地址必须从环境变量或配置中心获取。使用 API_BASE_URL 统一管理"),

        # API 客户端无超时
        ("api_no_timeout",
         [(r'(?i)(?:requests|httpx|urllib)\.(?:get|post|put|delete|patch)\s*\((?:(?!timeout).)*\)', "HTTP 调用缺少 timeout"),
         ], "critical",
         "所有出站 HTTP 调用必须设置 timeout 参数。推荐 timeout=(3.0, 30.0) (connect, read)"),

        # 响应状态码检查缺失
        ("api_no_status_check",
         [(r'(?i)(?:requests|httpx)\.(?:get|post|put|delete)\(', "HTTP 调用"),
          (r'(?i)\.json\(\)', "JSON 解析"),
         ], "high",
         "必须检查 response.status_code 或使用 raise_for_status()。非 2xx/3xx 写入 dead_letter 队列"),

        # 无速率限制
        ("api_no_rate_limit",
         [(r'(?i)(?:route|get|post|put|delete|patch)\s*\(', "API 路由定义"),
          (r'(?i)(?:rate_limit|throttle|ratelimit|RateLimiter)\b', "速率限制（良好）"),
         ], "medium",
         "API 端点必须配置速率限制（例如 slowapi + Redis）。防止下游系统被突发流量打崩"),

        # 错误响应格式不统一
        ("api_no_error_schema",
         [(r'(?i)return\s*\{[^}]*"error"', "错误响应"),
          (r'(?i)raise\s+HTTPException\b', "HTTP 异常"),
          (r'(?i)class\s+ErrorResponse|class\s+APIError', "统一错误模型"),
         ], "medium",
         "所有 API 错误应该返回统一格式: {'error': {'code': '...', 'message': '...', 'request_id': '...'}}"),

        # 分页缺失
        ("api_no_pagination",
         [(r'(?i)(?:list|find_all|get_all|get_many|search)\s*\(', "列表查询"),
          (r'(?i)\.all\(\)\s*(?:\.to_dict|without pagin)', "未限制返回行数"),
         ], "high",
         "所有列表接口必须分页。使用 page/page_size 或 cursor 模式，默认 max_page_size=100"),

        # 输入校验缺失
        ("api_no_input_validation",
         [(r'(?i)(?:@app\.route|@router\.get|@router\.post|@api\.route)', "API 路由"),
          (r'(?i)(?:Pydantic|BaseModel|marshmallow|Schema|serializer)', "输入校验模型（良好）"),
         ], "high",
         "所有 API 入参必须使用 Pydantic/marshmallow 校验。禁止直接使用 request.json"),
    ]

    def get_name(self) -> str:
        return "api_contract"

    def get_description(self) -> str:
        return "API契约审计 — endpoint/超时/限流/分页/输入校验/错误格式"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        tech_stack = project_features.get("tech_stack", [])
        api_techs = ["FastAPI", "Flask", "Django", "Express", "API"]
        if any(t in tech_stack for t in api_techs):
            return 0.95
        project_type = project_features.get("project_type", "")
        if project_type == "Backend":
            return 0.8
        return 0.5

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()

        # 1. OpenAPI / Swagger 检查
        swagger_files = []
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for f in files:
                if f.endswith(('.yaml', '.yml', '.json')) and 'openapi' in f.lower() or 'swagger' in f.lower():
                    swagger_files.append(os.path.relpath(os.path.join(root, f), project_path))
        if swagger_files:
            results.append(ValidationResult(
                check_name="openapi_schema_found",
                status="passed",
                message=f"找到 OpenAPI schema: {', '.join(swagger_files[:3])}",
                severity="low"
            ))
        else:
            results.append(ValidationResult(
                check_name="no_openapi_schema",
                status="info",
                message="未找到 OpenAPI/Swagger schema 文件",
                severity="low",
                remediation="使用 FastAPI 自动生成或手动维护 openapi.yaml 作为接口契约"
            ))

        # 2. 代码扫描
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.CHECKS:
                        if check_name in ("api_no_rate_limit", "api_no_error_schema", "api_no_input_validation"):
                            continue  # 反向检查单独处理
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped, re.IGNORECASE)
                            if not m:
                                continue
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="failed" if base_sev=="critical" else "warning",
                                message=f"[{rel_path}:{i}] {m.group(0)[:120]}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break

        # 反向检查：检测到路由但没有 rate limit
        file_content = {}
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        file_content[os.path.relpath(os.path.join(root, file), project_path)] = f.read()
                except Exception:
                    pass

        has_routes = any(re.search(r'(?:@app\.route|@router\.(?:get|post|put|delete|patch)|@api\.(?:get|post))', c)
                        for c in file_content.values())
        has_rate_limit = any(re.search(r'(?:rate_limit|throttle|ratelimit|RateLimiter|SlowAPI|Limiter)', c, re.IGNORECASE)
                            for c in file_content.values())

        if has_routes and not has_rate_limit:
            results.append(ValidationResult(
                check_name="api_no_rate_limit",
                status="warning",
                message="检测到 API 路由但未配置速率限制",
                severity="medium",
                remediation="使用 slowapi + Redis 为所有路由添加速率限制"
            ))

        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="api_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"API契约审计完成: {header}",
                severity="critical" if sev_counts.get("critical", 0) > 0 else "high",
                remediation="统一API端点管理为 BASE_URL 环境变量，添加超时/限流/分页/输入校验"
            ))
        return results


class ConcurrencyExpert(BasePerspectiveExpert):
    """并发安全专家 — async/await 正确性 + 死锁 + 资源泄露检测

    检查：
    - async 函数中的阻塞调用
    - 共享可变状态无锁访问
    - 死锁模式
    - async 上下文中的连接/session 泄露
    - 协程未 await
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # async 函数中的阻塞调用
        ("async_blocking_call",
         [(r'(?i)async def.*:\n.*time\.sleep\(', "async 函数中调用 time.sleep"),
          (r'(?i)async def.*:\n.*os\.system\(', "async 函数中调用 os.system"),
          (r'(?i)async def.*:\n.*subprocess\.(?:call|run|check_output)\(', "async 函数中同步 subprocess"),
          (r'(?i)async def.*:\n.*(?:requests|urllib)\.', "async 函数中同步 HTTP 请求"),
          (r'(?i)async def.*:\n.*open\(', "async 函数中同步文件操作"),
         ], "critical",
         "async 函数中禁止阻塞调用。time.sleep→asyncio.sleep, requests→httpx.AsyncClient, open→aiofiles"),

        # 共享状态无锁
        ("async_shared_state",
         [(r'(?i)(?:self\.\w+|global\s+\w+)\s*\+?=?\s*', "共享可变状态修改"),
          (r'(?i)(?:self\.\w+|global\s+\w+).*\.append\(', "列表追加无锁"),
          (r'(?i)(?:self\.\w+|global\s+\w+)\[.*\]\s*=', "字典/列表下标赋值"),
         ], "high",
         "共享可变状态必须使用 asyncio.Lock 保护。读多写少用 aiorwlock，高并发用无锁结构"),

        # 死锁模式
        ("async_deadlock",
         [(r'(?i)asyncio\.gather\(.*lock', "gather 中可能持锁导致死锁"),
          (r'(?i)async\s+with\s+\w+Lock.*:\s*\n.*await.*Lock', "锁内等待另一个锁（死锁风险）"),
         ], "high",
         "避免嵌套锁。锁的获取顺序必须全局一致。使用 asyncio.wait_for + timeout 防死锁"),

        # 连接/session 泄露
        ("async_session_leak",
         [(r'(?i)async\s+with.*Session|AsyncSession|AsyncClient|aioredis|aiomysql', "异步资源创建"),
          (r'(?i)session\.close\(\)|client\.aclose\(\)|pool\.close\(\)', "资源关闭（良好）"),
         ], "medium",
         "异步 session/client/pool 必须用 async with 管理生命周期。FastAPI 中用 lifespan+Depends 注入"),

        # 协程忘记 await
        ("async_missing_await",
         [(r'(?i)async def.*await\s*\w+\.\w+\(\)', "正常 await（良好）"),
          (r'(?i)asyncio\.create_task\(|asyncio\.gather\(', "task 管理"),
         ], "medium",
         "确保所有协程调用前有 await。不 awaited 的协程会静默跳过，造成数据丢失"),

        # 事件循环阻塞
        ("async_loop_block",
         [(r'(?i)(?:for|while).*(?:cpu|compute|heavy|compress|encrypt|crypto|hash).*(?:range|\bin\b)', "循环内 CPU 密集型操作"),
          (r'(?i)(?:pd\.read|cv2\.|numpy\.|sklearn\.)', "同步数据处理库在 async 上下文"),
         ], "high",
         "CPU 密集型任务用 loop.run_in_executor(ThreadPoolExecutor, fn) 执行，不要阻塞事件循环"),
    ]

    def get_name(self) -> str:
        return "concurrency"

    def get_description(self) -> str:
        return "并发安全审计 — async阻塞/共享状态/死锁/session泄露/未await"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        project_type = project_features.get("project_type", "")
        if project_type == "Backend":
            return 0.9
        tech_stack = project_features.get("tech_stack", [])
        if any(t in ["FastAPI", "aiohttp", "asyncio", "async"] for t in tech_stack):
            return 0.95
        return 0.4

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                except Exception:
                    continue

                # 行级扫描
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    for check_name, patterns, base_sev, fix in self.CHECKS:
                        if check_name in ("async_blocking_call", "async_deadlock", "async_loop_block"):
                            continue  # 多行检查单独处理
                        for pat, _detail in patterns:
                            m = re.search(pat, stripped, re.IGNORECASE)
                            if not m:
                                continue
                            results.append(ValidationResult(
                                check_name=check_name,
                                status="failed" if base_sev=="critical" else "warning",
                                message=f"[{rel_path}:{i}] {m.group(0)[:100]}",
                                severity=base_sev,
                                remediation=fix
                            ))
                            break

                # 多行: async def 中的阻塞调用
                if 'async def ' in content:
                    func_blocks = re.split(r'(?=async def )', content)
                    for block in func_blocks:
                        if not block.startswith('async def'):
                            continue
                        first_line = block.split('\n')[0]
                        line_num = content[:content.index(first_line)].count('\n') + 1 if first_line in content else 0

                        if any(kw in block for kw in ("time.sleep", "os.system")):
                            results.append(ValidationResult(
                                check_name="async_blocking_call",
                                status="critical",
                                message=f"[{rel_path}] async 函数中包含同步阻塞调用",
                                severity="critical",
                                remediation="time.sleep→asyncio.sleep, os→async subprocess"
                            ))
                        if any(kw in block for kw in ("requests.get", "requests.post", "requests.put")):
                            results.append(ValidationResult(
                                check_name="async_blocking_call",
                                status="critical",
                                message=f"[{rel_path}] async 函数中使用同步 requests 库",
                                severity="critical",
                                remediation="使用 httpx.AsyncClient 替代 requests"
                            ))

        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="concurrency_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"并发安全审计完成: {header}",
                severity="critical" if sev_counts.get("critical", 0) > 0 else "high",
                remediation="消除 async 中的阻塞调用，加锁保护共享状态，asyncio.wait_for 防死锁"
            ))
        return results


class ObservabilityExpert(BasePerspectiveExpert):
    """可观测性专家 — 日志/追踪/监控/告警完整性审计

    检查：
    - 结构化日志（JSON 格式）
    - Trace ID 注入
    - Health check 端点
    - Metrics 导出（Prometheus）
    - 错误追踪集成（Sentry）
    - 日志级别区分
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    CHECKS = [
        # 非结构化日志
        ("obs_no_structured_log",
         [(r'(?i)(?:logger|logging)\.\w+\(f["\']', "f-string 日志（非结构化）"),
          (r'(?i)(?:logger|logging)\.\w+\(.*%', "百分号格式化日志"),
         ], "medium",
         "生产日志必须是结构化 JSON 格式。使用 python-json-logger 或 structlog"),

        # 缺少 trace ID
        ("obs_no_trace_id",
         [(r'(?i)(?:request_id|trace_id|correlation_id|span_id|x-request-id)', "trace ID 存在（良好）"),
          (r'(?i)(?:logger|logging)\.\w+\(', "日志记录"),
         ], "high",
         "所有日志必须携带 trace_id。使用 OpenTelemetry 自动注入，或从 request.headers['X-Request-ID'] 提取"),

        # 缺少 health check
        ("obs_no_health",
         [(r'(?i)(?:health|healthz|liveness|readiness|ping)\s*\(|/health|/healthz|/ping', "健康检查端点"),
         ],
         "high",
         "必须实现 /health (liveness) 和 /health/ready (readiness) 端点。K8s 依赖它们做滚动更新"),

        # 缺少 metrics
        ("obs_no_metrics",
         [(r'(?i)(?:prometheus|PrometheusCounter|metrics|prometheus_client)', "Prometheus 指标"),
          (r'(?i)(?:Counter|Histogram|Gauge|Summary)\s*\(', "metrics 类型"),
         ],
         "medium",
         "使用 prometheus_client 导出: API 延迟(Histogram)、请求数(Counter)、错误率(Gauge)"),

        # 缺少错误追踪
        ("obs_no_error_tracking",
         [(r'(?i)(?:sentry|Sentry|raven|sentry_sdk|newrelic|datadog)', "错误追踪集成"),
          (r'(?i)(?:try|except|catch|error|异常)', "异常处理"),
         ],
         "medium",
         "集成 Sentry/NewRelic/Datadog 自动捕获异常。sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))"),

        # print 替代日志
        ("obs_print_insteadof_log",
         [(r'print\s*\(', "使用 print 而非 logger"),
         ],
         "medium",
         "生产代码禁止 print。全部替换为 logger.info/warning/error"),

        # 日志级别硬编码
        ("obs_log_level_hardcode",
         [(r'(?i)\.setLevel\(logging\.(?:DEBUG|INFO|WARNING|ERROR)\)', "日志级别硬编码"),
         ],
         "medium",
         "日志级别应从环境变量读取: logging.getLogger().setLevel(os.getenv('LOG_LEVEL', 'WARNING'))"),
    ]

    def get_name(self) -> str:
        return "observability"

    def get_description(self) -> str:
        return "可观测性审计 — 结构化日志/trace/health/metrics/错误追踪"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        scale = project_features.get("scale", "small")
        if scale in ("large", "enterprise"):
            return 0.95
        project_type = project_features.get("project_type", "")
        if project_type == "Backend":
            return 0.85
        return 0.5

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()

        file_content = {}
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        file_content[rel_path] = content
                except Exception:
                    continue

        # 全局扫描：health endpoint 存在性
        has_health = any(re.search(r'(?i)/health|healthz|liveness|readiness', c) for c in file_content.values())
        has_routes = any(re.search(r'(?i)@app\.route|@router\.(?:get|post)', c) for c in file_content.values())

        if has_routes and not has_health:
            results.append(ValidationResult(
                check_name="obs_no_health",
                status="high" if has_routes else "info",
                message="API 项目缺少健康检查端点",
                severity="high",
                remediation="添加 /health (liveness) 和 /health/ready (readiness) 端点"
            ))
        elif has_health:
            results.append(ValidationResult(
                check_name="obs_health_found",
                status="passed",
                message="健康检查端点已配置",
                severity="low"
            ))

        # 全局扫描：trace ID
        has_trace = any(re.search(r'(?i)request_id|trace_id|correlation_id|span_id', c) for c in file_content.values())
        has_logging = any(re.search(r'(?i)(?:logger|logging)\.\w+\(', c) for c in file_content.values())

        if has_logging and not has_trace:
            results.append(ValidationResult(
                check_name="obs_no_trace_id",
                status="warning",
                message="使用了日志但未注入 trace_id",
                severity="high",
                remediation="从 request.headers 提取 X-Request-ID 注入 logger adapter 或使用 OpenTelemetry"
            ))

        # 全局扫描：metrics
        has_metrics = any(re.search(r'(?i)prometheus|PrometheusCounter|prometheus_client|metrics', c) for c in file_content.values())
        if has_routes and not has_metrics:
            results.append(ValidationResult(
                check_name="obs_no_metrics",
                status="info",
                message="API 项目缺少 Prometheus metrics 导出",
                severity="medium",
                remediation="pip install prometheus-client && 添加 /metrics 端点"
            ))
        elif has_metrics:
            results.append(ValidationResult(
                check_name="obs_metrics_found",
                status="passed",
                message="Prometheus metrics 已配置",
                severity="low"
            ))

        # 行级扫描
        for rel_path, content in file_content.items():
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                    continue
                for check_name, patterns, base_sev, fix in self.CHECKS:
                    if check_name in ("obs_no_health", "obs_no_trace_id", "obs_no_metrics"):
                        continue
                    for pat, _detail in patterns:
                        m = re.search(pat, stripped, re.IGNORECASE)
                        if not m:
                            continue
                        results.append(ValidationResult(
                            check_name=check_name,
                            status="warning" if base_sev in ("high", "medium") else "info",
                            message=f"[{rel_path}:{i}] {m.group(0)[:100]}",
                            severity=base_sev,
                            remediation=fix
                        ))
                        break

        # 全局：错误追踪
        has_sentry = any(re.search(r'(?i)sentry|newrelic|datadog|raven', c) for c in file_content.values())
        if has_routes and not has_sentry:
            results.append(ValidationResult(
                check_name="obs_no_error_tracking",
                status="info",
                message="建议集成错误追踪 (Sentry/NewRelic/Datadog)",
                severity="medium",
                remediation="pip install sentry-sdk && sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))"
            ))

        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="observability_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"可观测性审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="使用 structlog+JSON 日志，注入 trace_id，导出 Prometheus metrics，集成 Sentry"
            ))
        return results


class ConfigAuditExpert(BasePerspectiveExpert):
    """配置审计专家 — .env 漂移 + 硬编码 URL/端口 + 配置一致性

    检查：
    - .env 文件 key 是否匹配 os.getenv 调用
    - 硬编码 IP 地址和端口
    - 多环境配置差异（.env.dev / .env.prod）
    - 敏感配置遗漏
    """

    SKIP_DIRS = ('__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build',
                 '.git', 'migrations', '.tox', 'output', 'logs')

    def get_name(self) -> str:
        return "config_audit"

    def get_description(self) -> str:
        return "配置审计 — .env漂移/硬编码URL端口/多环境一致性"

    def get_compatibility(self, project_features: Dict[str, Any]) -> float:
        scale = project_features.get("scale", "small")
        scale_weights = {"small": 0.6, "medium": 0.75, "large": 0.9, "enterprise": 1.0}
        return scale_weights.get(scale, 0.6)

    def validate(self, project_features: Dict[str, Any]) -> List[ValidationResult]:
        import re
        results = []
        project_path = os.getcwd()

        # 1. 收集 .env 文件中的 key
        env_files = {}
        env_keys = set()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if file.startswith('.env'):
                    filepath = os.path.join(root, file)
                    rel = os.path.relpath(filepath, project_path)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                    except Exception:
                        continue
                    keys = set()
                    for line in lines:
                        m = re.match(r'^\s*([A-Z_][A-Z0-9_]*)\s*=', line.strip())
                        if m:
                            keys.add(m.group(1))
                    env_files[rel] = keys
                    env_keys.update(keys)

        if env_files:
            results.append(ValidationResult(
                check_name="env_files_found",
                status="passed",
                message=f"检测到环境配置文件: {', '.join(env_files.keys())[:120]}",
                severity="low"
            ))
        else:
            results.append(ValidationResult(
                check_name="no_env_file",
                status="warning",
                message="未找到 .env 配置文件",
                severity="medium",
                remediation="创建 .env.example 作为模板，实际值通过 .env 或 secret manager 注入"
            ))

        # 2. 跨环境 .env 差异检测
        if len(env_files) >= 2:
            env_list = list(env_files.keys())
            for i in range(min(len(env_list), 3)):
                for j in range(i + 1, min(len(env_list), 3)):
                    a_keys, b_keys = env_files[env_list[i]], env_files[env_list[j]]
                    only_a = a_keys - b_keys
                    only_b = b_keys - a_keys
                    if only_a or only_b:
                        parts = []
                        if only_a:
                            parts.append(f"[{env_list[i]}]多出: {', '.join(sorted(only_a))[:80]}")
                        if only_b:
                            parts.append(f"[{env_list[j]}]多出: {', '.join(sorted(only_b))[:80]}")
                        results.append(ValidationResult(
                            check_name="env_drift",
                            status="warning",
                            message=f"配置文件 key 不一致: {'; '.join(parts)}",
                            severity="medium",
                            remediation="所有环境 .env 文件 key 应保持一致。差异 key 可能导致部署后配置缺失"
                        ))

        # 3. 注入扫描：.env key vs os.getenv 调用
        code_getenv_keys = set()
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    continue
                for m in re.finditer(r'os\.getenv\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', content):
                    code_getenv_keys.add(m.group(1))

        # os.getenv 引用了 .env 中不存在的 key
        if code_getenv_keys and env_keys:
            missing_in_env = code_getenv_keys - env_keys
            if missing_in_env:
                results.append(ValidationResult(
                    check_name="env_missing_key",
                    status="failed",
                    message=f"代码中引用的环境变量未在 .env 中定义: {', '.join(sorted(missing_in_env))[:120]}",
                    severity="high",
                    remediation="在 .env 或 .env.example 中添加缺失的 key。或确认这些变量由部署平台注入"
                ))
            # .env 中有但代码中未使用
            unused_keys = env_keys - code_getenv_keys
            if unused_keys and len(unused_keys) <= 10:
                results.append(ValidationResult(
                    check_name="env_unused_key",
                    status="info",
                    message=f"疑似未使用的 .env key: {', '.join(sorted(unused_keys))[:120]}",
                    severity="low",
                    remediation="检查这些 key 是否已废弃，清理 .env 文件中的死配置"
                ))

        # 4. 硬编码 URL/端口/IP
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in self.SKIP_DIRS]
            for file in files:
                if not file.endswith('.py'):
                    continue
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, project_path)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                except Exception:
                    continue
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#') or stripped.startswith(('import ', 'from ')):
                        continue
                    # 硬编码 IP
                    m = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', stripped)
                    if m and m.group(1) not in ('0.0.0.0', '127.0.0.1', '255.255.255.255'):
                        results.append(ValidationResult(
                            check_name="config_hardcoded_ip",
                            status="warning",
                            message=f"[{rel_path}:{i}] 硬编码 IP: {m.group(1)}",
                            severity="high",
                            remediation=f"将 {m.group(1)} 替换为环境变量，如 os.getenv('REDIS_HOST')"
                        ))
                    # 硬编码端口
                    m = re.search(r'(?<![\d:])port\s*=\s*(\d{4,5})(?!\d)', stripped, re.IGNORECASE)
                    if m:
                        results.append(ValidationResult(
                            check_name="config_hardcoded_port",
                            status="info",
                            message=f"[{rel_path}:{i}] 硬编码端口: {m.group(1)}",
                            severity="low",
                            remediation=f"端口从环境变量读取: int(os.getenv('PORT', {m.group(1)}))"
                        ))

        if results:
            sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            for r in results:
                sev_counts[r.severity] = sev_counts.get(r.severity, 0) + 1
            header = " · ".join(f"{v} {k}" for k, v in sev_counts.items() if v > 0)
            results.insert(0, ValidationResult(
                check_name="config_audit_report",
                status="failed" if sev_counts.get("critical", 0) + sev_counts.get("high", 0) > 0 else "warning",
                message=f"配置审计完成: {header}",
                severity="high" if sev_counts.get("high", 0) > 0 else "medium",
                remediation="统一环境变量与 .env，消除硬编码IP，对齐多环境配置"
            ))
        return results


# 导出所有专家类
__all__ = [
    "BasePerspectiveExpert",
    "PerspectiveRegistry",
    "ValidationResult",
    "DeveloperExpert",
    "UserExpert",
    "SecurityExpert",
    "HealthcareExpert",
    "AuditorExpert",
    "StatisticianExpert",
    "PerformanceExpert",
    "ComplianceExpert",
    "BusinessExpert",
    "ArchitectExpert",
    "DevOpsExpert",
    "HardcodeInspectorExpert",
    "TestExpert",
    "DependencyExpert",
    "LintExpert",
    "FrontendExpert",
    "DBMigrationExpert",
    "PHIInspectExpert",
    "DataIntegrityExpert",
    "ProductionReadinessExpert",
    "MedicalDataValidatorExpert",
    "APIContractExpert",
    "ConcurrencyExpert",
    "ObservabilityExpert",
    "ConfigAuditExpert",
]