"""项目扫描器 - 自动识别项目特征"""

import os
import re
from typing import Dict, List, Any

from .models import ProjectProfile


class ProjectScanner:
    """智能项目扫描器"""
    
    def __init__(self):
        # 技术栈特征映射
        self.tech_stack_patterns = {
            "Python": [r"\.py$"],
            "TypeScript": [r"\.ts$", r"\.tsx$"],
            "JavaScript": [r"\.js$", r"\.jsx$"],
            "React": ["react", "next"],
            "Vue": ["vue"],
            "FastAPI": ["fastapi"],
            "Django": ["django"],
            "SQLAlchemy": ["sqlalchemy"],
            "PostgreSQL": ["postgresql", "psycopg"],
            "Redis": ["redis"],
            "Docker": ["Dockerfile", "docker-compose"],
            "Node.js": ["package.json", "node_modules"],
        }
        
        # 项目类型特征
        self.project_type_patterns = {
            "Web": ["frontend", "src", "public", "index.html"],
            "Mobile": ["android", "ios", "mobile"],
            "Desktop": ["electron", "desktop"],
            "Data": ["data", "pandas", "numpy", "spark"],
            "AI": ["tensorflow", "pytorch", "scikit-learn", "llm", "gpt"],
            "Backend": ["api", "backend", "server"],
            "Embedded": ["embedded", "firmware", "arduino"],
        }
        
        # 领域特征
        self.domain_patterns = {
            "金融": ["finance", "bank", "stock", "fund", "investment"],
            "医疗": ["healthcare", "medical", "hospital", "patient", "clinic", "disease"],
            "电商": ["ecommerce", "shop", "store", "product"],
            "教育": ["education", "learning", "course", "school"],
            "政府": ["government", "gov", "public"],
            "社交": ["social", "chat", "community"],
        }
    
    def scan(self, project_path: str) -> ProjectProfile:
        """扫描项目并提取特征"""
        features = self._extract_features(project_path)
        
        return ProjectProfile(
            project_type=features["project_type"],
            tech_stack=features["tech_stack"],
            complexity=features["complexity"],
            scale=features["scale"],
            domain=features["domain"],
            security_requirements=features["security_requirements"],
            file_count=features["file_count"],
            lines_of_code=features["lines_of_code"],
        )
    
    def _extract_features(self, project_path: str) -> Dict[str, Any]:
        """提取项目特征"""
        files = self._get_all_files(project_path)
        file_count = len(files)
        lines_of_code = self._count_lines(project_path)
        
        # 检测技术栈
        tech_stack = self._detect_tech_stack(files)
        
        # 检测项目类型
        project_type = self._detect_project_type(files)
        
        # 检测领域
        domain = self._detect_domain(files)
        
        # 评估规模和复杂度
        scale = self._estimate_scale(file_count, lines_of_code)
        complexity = self._estimate_complexity(file_count, lines_of_code, tech_stack)
        
        # 评估安全要求
        security_requirements = self._estimate_security_requirements(domain, project_type)
        
        return {
            "project_type": project_type,
            "tech_stack": tech_stack,
            "complexity": complexity,
            "scale": scale,
            "domain": domain,
            "security_requirements": security_requirements,
            "file_count": file_count,
            "lines_of_code": lines_of_code,
        }
    
    def _get_all_files(self, project_path: str) -> List[str]:
        """获取所有文件路径"""
        files = []
        for root, dirs, filenames in os.walk(project_path):
            # 排除一些目录
            dirs[:] = [d for d in dirs if d not in [
                '.git', 'node_modules', '__pycache__', 'venv', '.venv',
                'dist', 'build', 'output', 'logs'
            ]]
            
            for filename in filenames:
                files.append(os.path.join(root, filename))
        
        return files
    
    def _count_lines(self, project_path: str) -> int:
        """计算代码行数"""
        lines = 0
        for root, dirs, filenames in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in [
                '.git', 'node_modules', '__pycache__', 'venv', '.venv'
            ]]
            
            for filename in filenames:
                if filename.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    try:
                        with open(os.path.join(root, filename), 'r', encoding='utf-8', errors='ignore') as f:
                            lines += len(f.readlines())
                    except:
                        pass
        
        return lines
    
    def _detect_tech_stack(self, files: List[str]) -> List[str]:
        """检测技术栈"""
        detected = []
        
        for tech, patterns in self.tech_stack_patterns.items():
            for pattern in patterns:
                for filepath in files:
                    filename = os.path.basename(filepath).lower()
                    content = ""
                    
                    # 检查文件名
                    if re.search(pattern.lower(), filename):
                        detected.append(tech)
                        break
                    
                    # 检查文件内容（对于配置文件）
                    if filename in ['package.json', 'requirements.txt', 'pyproject.toml']:
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().lower()
                                if pattern.lower() in content:
                                    detected.append(tech)
                                    break
                        except:
                            pass
            
            if tech in detected:
                continue
        
        return sorted(list(set(detected)))
    
    def _detect_project_type(self, files: List[str]) -> str:
        """检测项目类型"""
        for project_type, patterns in self.project_type_patterns.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()
                for filepath in files:
                    path_lower = filepath.lower()
                    if pattern_lower in path_lower:
                        return project_type
        
        # 默认返回Web
        return "Web"
    
    def _detect_domain(self, files: List[str]) -> str:
        """检测业务领域"""
        for domain, keywords in self.domain_patterns.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                for filepath in files:
                    filename = os.path.basename(filepath).lower()
                    if keyword_lower in filename:
                        return domain
                    
                    # 检查文件内容（README, docs）
                    if filename in ['readme.md', 'readme.txt', 'docs']:
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read().lower()
                                if keyword_lower in content:
                                    return domain
                        except:
                            pass
        
        return "通用"
    
    def _estimate_scale(self, file_count: int, lines_of_code: int) -> str:
        """评估项目规模"""
        if lines_of_code > 100000 or file_count > 500:
            return "enterprise"
        elif lines_of_code > 10000 or file_count > 100:
            return "large"
        elif lines_of_code > 1000 or file_count > 20:
            return "medium"
        else:
            return "small"
    
    def _estimate_complexity(self, file_count: int, lines_of_code: int, tech_stack: List[str]) -> str:
        """评估项目复杂度"""
        complexity_score = 0
        
        # 基于代码量
        if lines_of_code > 50000:
            complexity_score += 3
        elif lines_of_code > 10000:
            complexity_score += 2
        elif lines_of_code > 1000:
            complexity_score += 1
        
        # 基于技术栈复杂度
        complex_techs = ["AI", "Data", "Embedded", "Docker"]
        for tech in tech_stack:
            if tech in complex_techs:
                complexity_score += 1
        
        # 基于文件数量
        if file_count > 200:
            complexity_score += 2
        elif file_count > 50:
            complexity_score += 1
        
        if complexity_score >= 5:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _estimate_security_requirements(self, domain: str, project_type: str) -> int:
        """评估安全要求等级"""
        score = 5  # 默认中等
        
        # 领域因素
        high_security_domains = ["金融", "医疗", "政府"]
        if domain in high_security_domains:
            score += 3
        
        # 项目类型因素
        if project_type in ["Web", "Mobile"]:
            score += 1
        
        return min(10, max(1, score))