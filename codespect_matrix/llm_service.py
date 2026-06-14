"""大模型服务模块 - 支持多种大模型提供商的统一接口"""

import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMService:
    """大模型服务封装类"""
    
    def __init__(self, provider: str = None, api_key: str = None, model: str = None):
        """
        初始化大模型服务
        
        Args:
            provider: 模型提供商 (openai, anthropic, google, baidu, tongyi, zhipu, huggingface)
            api_key: API密钥
            model: 模型名称
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_default_model()
        self.client = self._init_client()
        
    def _get_api_key(self) -> str:
        """根据提供商获取API密钥"""
        key_map = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "baidu": os.getenv("BAIDU_API_KEY"),
            "tongyi": os.getenv("TONGYI_API_KEY"),
            "zhipu": os.getenv("ZHIPU_API_KEY"),
            "huggingface": os.getenv("HUGGINGFACE_API_KEY"),
        }
        return key_map.get(self.provider)
    
    def _get_default_model(self) -> str:
        """获取默认模型名称"""
        model_map = {
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            "google": os.getenv("GOOGLE_MODEL", "gemini-pro"),
            "baidu": os.getenv("BAIDU_MODEL", "ERNIE-Bot-4.0"),
            "tongyi": os.getenv("TONGYI_MODEL", "qwen-plus"),
            "zhipu": os.getenv("ZHIPU_MODEL", "glm-4"),
            "huggingface": os.getenv("HUGGINGFACE_MODEL", "mistralai/Mistral-7B-v0.3"),
        }
        return model_map.get(self.provider, "gpt-4o-mini")
    
    def _init_client(self):
        """初始化客户端"""
        if not self.api_key:
            raise ValueError(f"未配置 {self.provider} 的 API 密钥")
        
        try:
            if self.provider == "openai":
                from openai import OpenAI
                base_url = os.getenv("OPENAI_API_BASE")
                return OpenAI(api_key=self.api_key, base_url=base_url)
            
            elif self.provider == "anthropic":
                from anthropic import Anthropic
                return Anthropic(api_key=self.api_key)
            
            elif self.provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                return genai.GenerativeModel(self.model)
            
            elif self.provider == "baidu":
                from qianfan import ChatCompletion
                return ChatCompletion
            
            elif self.provider == "tongyi":
                from dashscope import Generation
                return Generation
            
            elif self.provider == "zhipu":
                from zhipuai import ZhipuAI
                return ZhipuAI(api_key=self.api_key)
            
            elif self.provider == "huggingface":
                from transformers import pipeline
                return pipeline("text-generation", model=self.model)
            
            else:
                raise ValueError(f"不支持的模型提供商: {self.provider}")
                
        except ImportError as e:
            raise ImportError(f"缺少 {self.provider} 的依赖库: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 提示词
            **kwargs: 额外参数（temperature, max_tokens等）
        
        Returns:
            生成的文本
        """
        temperature = kwargs.get("temperature", float(os.getenv("OPENAI_TEMPERATURE", "0.7")))
        max_tokens = kwargs.get("max_tokens", int(os.getenv("OPENAI_MAX_TOKENS", "4096")))
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response.content[0].text
            
            elif self.provider == "google":
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    },
                )
                return response.text
            
            elif self.provider == "baidu":
                response = self.client.do(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.get("result", {}).get("content", "")
            
            elif self.provider == "tongyi":
                response = self.model.call(
                    model=self.model,
                    input=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.output.text
            
            elif self.provider == "zhipu":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            
            elif self.provider == "huggingface":
                response = self.client(
                    prompt,
                    max_length=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                )
                return response[0]["generated_text"]
            
            else:
                raise ValueError(f"不支持的模型提供商: {self.provider}")
                
        except Exception as e:
            raise RuntimeError(f"大模型调用失败: {e}")
    
    def analyze_project(self, project_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用大模型分析项目特征
        
        Args:
            project_features: 项目特征字典
        
        Returns:
            分析结果
        """
        prompt = f"""
        作为一位资深的软件架构师和质量保证专家，请分析以下项目特征：
        
        项目信息：
        - 项目类型: {project_features.get('project_type', '')}
        - 技术栈: {', '.join(project_features.get('tech_stack', []))}
        - 规模: {project_features.get('scale', '')}
        - 复杂度: {project_features.get('complexity', '')}
        - 业务领域: {project_features.get('domain', '')}
        - 安全要求等级: {project_features.get('security_requirements', 5)}/10
        - 文件数量: {project_features.get('file_count', 0)}
        - 代码行数: {project_features.get('lines_of_code', 0)}
        
        请提供以下分析：
        1. 项目质量风险评估（高/中/低风险领域）
        2. 推荐的质量检查重点
        3. 潜在的技术债务
        4. 优化建议
        
        请用JSON格式输出，包含risk_assessment, focus_areas, technical_debt, recommendations字段。
        """
        
        result = self.generate(prompt, temperature=0.3, max_tokens=2048)
        return self._parse_json(result)
    
    def generate_report(self, validation_results: List[Dict[str, Any]], project_profile: Dict[str, Any]) -> str:
        """
        使用大模型生成质量报告
        
        Args:
            validation_results: 验证结果列表
            project_profile: 项目特征
        
        Returns:
            格式化的报告文本
        """
        results_str = "\n".join([
            f"- [{r.get('severity', '')}] {r.get('check_name', '')}: {r.get('message', '')}"
            for r in validation_results
        ])
        
        prompt = f"""
        作为一位专业的质量保证工程师，请基于以下验证结果生成一份详细的质量报告：
        
        项目信息：
        - 项目类型: {project_profile.get('project_type', '')}
        - 技术栈: {', '.join(project_profile.get('tech_stack', []))}
        - 规模: {project_profile.get('scale', '')}
        - 领域: {project_profile.get('domain', '')}
        
        验证问题列表：
        {results_str}
        
        请生成一份专业的质量报告，包含：
        1. 执行摘要
        2. 问题分类统计
        3. 风险评估
        4. 修复建议优先级
        5. 改进路线图
        
        报告格式：markdown
        """
        
        return self.generate(prompt, temperature=0.5, max_tokens=4096)
    
    def recommend_perspectives(self, project_features: Dict[str, Any]) -> List[str]:
        """
        使用大模型推荐视角专家
        
        Args:
            project_features: 项目特征
        
        Returns:
            推荐的视角专家名称列表
        """
        prompt = f"""
        作为一位资深的软件测试专家，请根据以下项目特征推荐最合适的质量检查视角：
        
        项目特征：
        - 项目类型: {project_features.get('project_type', '')}
        - 技术栈: {', '.join(project_features.get('tech_stack', []))}
        - 规模: {project_features.get('scale', '')}
        - 复杂度: {project_features.get('complexity', '')}
        - 业务领域: {project_features.get('domain', '')}
        - 安全要求: {project_features.get('security_requirements', 5)}/10
        
        可用视角专家：
        1. developer - 代码质量、类型安全、架构设计
        2. user - 用户体验、可用性、界面友好性
        3. security - 漏洞扫描、渗透测试、数据加密
        4. healthcare - 医疗数据合规性、HIPAA合规、数据脱敏
        5. auditor - 合规性、可追溯性、审计日志
        6. statistician - 算法正确性、数据质量、模型验证
        7. performance - 负载测试、响应时间、资源消耗
        8. compliance - GDPR/ISO27001/行业标准合规
        9. business - 需求一致性、业务流程正确性
        10. architect - 系统架构、模块耦合、技术债务
        11. devops - 可观测性、容错能力、扩展性
        
        请按优先级推荐5个最合适的视角专家，只返回专家名称，用逗号分隔。
        """
        
        result = self.generate(prompt, temperature=0.2, max_tokens=100)
        return [s.strip() for s in result.split(",") if s.strip()]
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """解析JSON响应"""
        import json
        try:
            # 尝试提取JSON部分
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "JSON解析失败", "raw_response": text}


# 工厂函数
def create_llm_service(provider: str = None) -> LLMService:
    """
    创建大模型服务实例
    
    Args:
        provider: 模型提供商
    
    Returns:
        LLMService实例
    """
    return LLMService(provider)


# 全局单例
_llm_service = None

def get_llm_service() -> LLMService:
    """获取全局大模型服务实例"""
    global _llm_service
    if _llm_service is None:
        try:
            _llm_service = LLMService()
        except Exception as e:
            # 如果环境变量未配置，返回None（兼容Trae CN环境）
            return None
    return _llm_service


__all__ = ["LLMService", "create_llm_service", "get_llm_service"]