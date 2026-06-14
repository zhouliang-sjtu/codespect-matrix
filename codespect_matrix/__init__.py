"""codespect-matrix - AI驱动的智能质量校验引擎

通过大模型分析项目特征，动态识别最优验证视角，实现精准的多维度质量审计与工程优化。

核心特性：
- 智能项目扫描：自动分析项目结构、技术栈、规模和业务领域
- 大模型视角识别：基于项目特征动态推荐最合适的质量校验视角组合
- 动态专家系统：11种视角专家，自动适配不同项目类型
- 四阶段分层扫描：环境基线→静态分析→运行时验证→集成验证
- 智能问题分类：自动分类问题等级和类型，提供修复建议
- 质量报告生成：大模型驱动的专业质量报告自动生成

示例：
    from codespect_matrix import QAService
    
    qa_service = QAService()
    result = qa_service.validate()
    report = qa_service.generate_report()
"""

__version__ = "3.0.0"
__author__ = "周良"
__organization__ = "上海交通大学医学院"

from .core import QAService
from .scanner import ProjectScanner
from .models import ValidationResult, RoundResult, ProjectProfile
from .llm_service import LLMService, create_llm_service, get_llm_service
from .cli import main as cli_main
from .perspectives import (
    BasePerspectiveExpert,
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

__all__ = [
    "QAService",
    "ProjectScanner",
    "ValidationResult",
    "RoundResult",
    "ProjectProfile",
    "LLMService",
    "create_llm_service",
    "get_llm_service",
    "cli_main",
    "BasePerspectiveExpert",
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