---
name: "codespect-matrix"
version: "4.0.0"
description: "codespect-matrix — 26位视角专家矩阵式代码质量审计引擎"
author:
  name: "周良"
  email: "zhouliang@shsmu.edu.cn"
  organization: "上海交通大学医学院"
category: "开发工具"
tags:
  - "代码质量"
  - "自动化测试"
  - "工程优化"
  - "多视角分析"
  - "AI辅助开发"
  - "CI/CD"
  - "质量保证"
  - "安全审计"
  - "隐私合规"
  - "医疗信息化"
---

# codespect-matrix - AI驱动的智能质量校验引擎

## 产品概述

**codespect-matrix** 是一款基于大语言模型的智能质量校验工具，配备 **26 位视角专家**，通过全量代码扫描、CI 门禁、风险评分、增量 diff 和基线对比五大能力，将项目从粗胚打磨到生产可部署。

### 核心价值

| 维度 | 价值 |
|------|------|
| **全量覆盖** | 26 位专家默认全部运行，不留死角 |
| **CI 门禁** | `--ci` 自动判定 exit_code，集成 GitHub Actions |
| **风险量化** | 加权评分引擎，输出雷达图数据结构 |
| **增量扫描** | `--diff` 仅扫变更文件/行，秒级反馈 |
| **基线追踪** | `--baseline` 保存快照，`--baseline-diff` 对比趋势 |
| **迭代收敛** | 指纹追踪多轮运行，自动判定收敛 |
| **医疗专项** | PHI 隐私扫描、医学数据校验、HIPAA 合规 |

---

## 快速开始

```bash
# pip 安装
pip install https://github.com/zhouliang-sjtu/codespect-matrix/releases/download/v4.0.0/codespect_matrix-4.0.0-py3-none-any.whl

# 或源码安装
git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
cd codespect-matrix
pip install -e .
```

### 使用方式

#### 命令行 — 全量扫描（默认）

```bash
# 全量扫描（26 位专家全部运行）
codespect-matrix --round 1

# CI/CD 门禁模式
codespect-matrix --ci --json

# 增量扫描（仅 git diff 变更）
codespect-matrix --diff

# 风险评分
codespect-matrix --risk-score

# 建立基线 + 对比变化
codespect-matrix --baseline
# ...修改代码...
codespect-matrix --baseline-diff

# 完整收敛周期
codespect-matrix --full-cycle --report --output report.md
```

#### API 调用

```python
from codespect_matrix import QAService

qa = QAService(project_path="/path/to/project")

# 全量扫描（默认 26 位专家）
result = qa.validate(round_number=1)

# CI 门禁
gate = qa.ci_check()
print(f"Exit: {gate['exit_code']}, Risk: {gate['risk_score']['risk_level']}")

# 风险评分
score = qa.compute_risk_score(result.issues_found)
print(score["risk_level"], score["total_score"])

# 增量扫描
diff = qa.validate_diff(target_branch="HEAD~1")

# 基线对比
qa.save_baseline()
delta = qa.diff_baseline()
print(delta["delta"]["trend"])  # improving | stable | degrading
```

---

## 26 位视角专家

| 层级 | 专家 | 核心能力 |
|------|------|---------|
| **代码层** | developer | 编译检查、类型安全 |
| | hardcode_inspector | 硬编码检测、跨文件追踪 |
| | auditor | 异常处理审计、bare except |
| | linter | ruff/flake8/pylint/mypy |
| **测试层** | tester | pytest + 覆盖率分级 |
| | dependency | pip-audit 漏洞 + 过期依赖 |
| **安全层** | security | eval/注入/反序列化 7类 |
| | phi_inspector | PHI 日志泄露/导出未脱敏 |
| | compliance | 许可证/GPL依赖 |
| **数据层** | statistician | 过拟合/NaN/数据泄露 |
| | data_integrity | ETL行数/主键/外键 |
| | med_validator | 血压/ICD/身份证校验 |
| **架构层** | architect | 循环导入 + 大模块识别 |
| | api_contract | endpoint/超时/限流/分页 |
| | concurrency | async阻塞/死锁/session泄露 |
| | db_migration | Alembic同步/downgrade |
| **质量层** | performance | N+1/内存炸弹/阻塞IO |
| | business | README/CHANGELOG/.gitignore |
| | frontend | package.json/tsc/ESLint |
| | user | UI框架/组件库/可访问性 |
| **部署层** | devops | Docker/CI/.env.example |
| | production_readiness | 连接池/优雅关闭/幂等 |
| | observability | 结构化日志/trace/metrics |
| | config_audit | .env漂移/硬编码IP |
| **领域层** | healthcare | HIPAA/HL7 FHIR/脱敏 |

---

## 五大能力

| 能力 | CLI | 说明 |
|------|-----|------|
| **全量扫描** | `--round N` | 26 位专家全部运行（默认） |
| **CI 门禁** | `--ci --json` | critical>0 或 high>5 时 exit_code=1 |
| **风险评分** | `--risk-score` | 加权评分 + 雷达图数据 |
| **增量扫描** | `--diff` | git diff 变更文件/行级扫描 |
| **基线追踪** | `--baseline` / `--baseline-diff` | 保存基线 + 改善/恶化趋势 |

---

## 大模型支持

7 家厂商适配，未配置时自动降级为规则引擎模式：

| 提供商 | 配置 |
|---|---|
| OpenAI (GPT-4o) | `LLM_PROVIDER=openai` |
| Anthropic (Claude) | `LLM_PROVIDER=anthropic` |
| Google (Gemini) | `LLM_PROVIDER=google` |
| 百度文心一言 | `LLM_PROVIDER=baidu` |
| 阿里通义千问 | `LLM_PROVIDER=tongyi` |
| 智谱 GLM | `LLM_PROVIDER=zhipu` |
| Hugging Face | `LLM_PROVIDER=huggingface` |

---

## 医疗领域专项

| 检查项 | 说明 |
|---|---|
| PHI 隐私扫描 | 日志、print、异常、导出、API 中的患者信息泄露 |
| 医学数据校验 | 血压(60-260)、血氧(60-100)、ICD-10格式、身份证校验位 |
| ETL 数据完整性 | 行数校验、主键去重、外键孤儿、时间戳单调性 |
| 数据脱敏验证 | 姓名→假名、身份证→哈希、数据导出缺脱敏 |

---

## 问题分级

| 等级 | 权重 | 说明 |
|------|------|------|
| critical (P0) | 100 | 服务不可启动 / PHI泄露 / 编译失败 |
| high (P1) | 50 | 安全漏洞 / 数据不完整 / HTTP无超时 |
| medium (P2) | 15 | 不符合最佳实践 / 缺少限流/分页 |
| low (P3) | 3 | 优化建议 |

---

## CI/CD 集成 (GitHub Actions)

```yaml
- name: codespect-matrix gate
  run: codespect-matrix --ci --json > qa-report.json
  # exit_code 自动判定门禁是否通过
```

---

## 自定义扩展

```python
from codespect_matrix import BasePerspectiveExpert, ValidationResult

class MyExpert(BasePerspectiveExpert):
    def get_name(self):
        return "my_expert"
    
    def get_compatibility(self, profile):
        return 0.9
    
    def validate(self, profile):
        return [ValidationResult(
            check_name="my_check", status="warning",
            message="发现问题", severity="medium",
            remediation="修复建议"
        )]

qa = QAService()
qa.register_expert(MyExpert)
```

---

## CLI 命令参考

| 参数 | 说明 |
|------|------|
| `--path, -p` | 项目路径（默认当前目录） |
| `--round, -r` | 校验轮次 |
| `--full-cycle, -f` | 完整收敛周期 |
| `--analyze, -a` | 仅分析项目特征 |
| `--ci` | CI/CD 门禁模式 |
| `--json` | 输出 JSON 格式 |
| `--diff [TARGET]` | 增量扫描（默认 HEAD~1） |
| `--risk-score` | 风险评分 |
| `--baseline` | 保存基线 |
| `--baseline-diff` | 对比基线 |
| `--targeted` | 快速模式（仅 top-5 专家） |
| `--report, -o` | 生成报告 |
| `--output` | 报告输出路径 |

---

## 项目结构

```
codespect-matrix/
├── .env.example              # 环境配置模板（7种LLM + Sentry + Redis）
├── iterative_qa.yaml         # 策略配置（26位专家 + CI阈值）
├── pyproject.toml            # 构建配置
├── requirements.txt          # 依赖清单
├── SKILL.md                  # 技能规范
├── skill.yaml                # 技能元数据
├── codespect_matrix/
│   ├── __init__.py
│   ├── cli.py                # 命令行接口（12个子命令）
│   ├── core.py               # QAService + 5能力引擎
│   ├── scanner.py            # 项目特征扫描器
│   ├── models.py             # 数据模型
│   ├── llm_service.py        # 7家LLM适配层
│   └── perspectives/
│       └── __init__.py       # 26 位视角专家
```

---

## 免费 + 捐赠

codespect-matrix 完全免费。欢迎通过以下方式支持：
- ⭐ Star 这个项目
- 💰 [GitHub Sponsors](https://github.com/sponsors/zhouliang-sjtu)

---

## 许可证

MIT License © 2026 周良 · 上海交通大学医学院

---

**版本**: 4.0.0  
**状态**: 生产就绪  
**专家**: 26 位  
**能力**: 全量扫描 · CI 门禁 · 风险评分 · 增量 diff · 基线对比
