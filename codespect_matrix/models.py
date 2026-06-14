"""数据模型 - 定义项目特征和验证结果的数据结构"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    """验证结果"""
    check_name: str
    status: str  # passed, failed, warning, info
    message: str
    severity: str  # critical, high, medium, low
    remediation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "message": self.message,
            "severity": self.severity,
            "remediation": self.remediation,
        }


@dataclass
class RoundResult:
    """单轮校验结果"""
    round_number: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    issues_found: List[ValidationResult] = field(default_factory=list)
    issues_fixed: int = 0
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "timestamp": self.timestamp.isoformat(),
            "issues_found": [r.to_dict() for r in self.issues_found],
            "issues_fixed": self.issues_fixed,
            "status": self.status,
        }


@dataclass
class ProjectProfile:
    """项目特征分析结果"""
    project_type: str
    tech_stack: List[str]
    complexity: str  # low, medium, high
    scale: str       # small, medium, large, enterprise
    domain: str      # 业务领域
    security_requirements: int  # 0-10
    file_count: int
    lines_of_code: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_type": self.project_type,
            "tech_stack": self.tech_stack,
            "complexity": self.complexity,
            "scale": self.scale,
            "domain": self.domain,
            "security_requirements": self.security_requirements,
            "file_count": self.file_count,
            "lines_of_code": self.lines_of_code,
        }


__all__ = ["ValidationResult", "RoundResult", "ProjectProfile"]