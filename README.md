<p align="center">
  <h1 align="center">codespect-matrix</h1>
  <p align="center"><strong>codespect-matrix — 26位视角专家矩阵式代码质量审计引擎</strong></p>
  <p align="center">
    <img src="https://img.shields.io/badge/version-4.0.0-blue" alt="Version">
    <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="License">
    <img src="https://img.shields.io/badge/status-production-success" alt="Status">
    <img src="https://img.shields.io/badge/experts-26-orange" alt="Experts">
  </p>
  <p align="center">
    26 位 AI 专家全量扫描 · CI 门禁 · 风险评分 · 增量 diff · 基线对比
  </p>
</p>

---

## 一句话介绍

> 不是又一个 Linter。**codespect-matrix** 像一支虚拟的 QA 团队——让 26 位 AI 视角专家围绕你的项目展开多轮交叉审查，直到所有问题收敛，再输出可执行的质量报告和风险评分。

---

## 解决什么痛点？

| 传统质量检查 | codespect-matrix |
|---|---|
| 单一视角（Linter / 单测覆盖） | 26 种视角专家全量联合审查 |
| 规则死板，配置繁琐 | AI 动态适配项目特征，默认全量运行 |
| 只报错，不给修复路径 | 每一条 issue 附带 remediation |
| 一次扫完就结束 | **迭代收敛**——跑多轮直到无新问题 |
| 不能做 CI 拦截 | `--ci` 出口码 + JSON，直接嵌入 GitHub Actions |
| 没法量化质量变化 | `--baseline` 保存快照，`--baseline-diff` 对比趋势 |
| 通用工具，不懂你的行业 | 内置 PHI 隐私 / 医学校验 / HIPAA 等医疗领域专项 |

**核心逻辑**：扫描项目 → 26 位专家全量运行 → 风险评分 + CI 门禁判定 → 迭代收敛 → 输出报告。

---

## 30 秒上手

```bash
# 安装
pip install https://github.com/zhouliang-sjtu/codespect-matrix/releases/download/v4.0.0/codespect_matrix-4.0.0-py3-none-any.whl

# 一行全量扫描（26 位专家全部运行）
codespect-matrix

# CI 门禁
codespect-matrix --ci --json

# 增量扫描
codespect-matrix --diff

# 完整收敛周期
codespect-matrix --full-cycle --report --output report.md
```

<details>
<summary> 源码安装</summary>

```bash
git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
cd codespect-matrix
pip install -e .
```
</details>

---

## 核心能力

### 26 位视角专家（全量运行）

| 层级 | 专家 | 核心能力 |
|------|------|---------|
| **代码层** | developer | 编译检查、类型安全 |
| | hardcode_inspector | 硬编码检测、跨文件追踪 |
| | auditor | 异常审计、bare except |
| | linter | ruff/flake8/pylint/mypy |
| **测试层** | tester | pytest + 覆盖率 |
| | dependency | pip-audit + 过期依赖 |
| **安全层** | security | eval/注入/反序列化 |
| | phi_inspector | PHI 隐私扫描 |
| | compliance | 许可证/GPL |
| **数据层** | statistician | 过拟合/NaN/数据泄露 |
| | data_integrity | ETL 行数/主键/外键 |
| | med_validator | 血压/ICD/身份证 |
| **架构层** | architect | 循环导入/大模块 |
| | api_contract | endpoint/限流/分页 |
| | concurrency | async阻塞/死锁 |
| | db_migration | Alembic/downgrade |
| **质量层** | performance | N+1/内存炸弹/阻塞IO |
| | business | README/CHANGELOG |
| | frontend | pkg.json/tsc/ESLint |
| | user | UI框架/可访问性 |
| **部署层** | devops | Docker/CI/.env.example |
| | production_readiness | 连接池/优雅关闭/幂等 |
| | observability | 结构化日志/trace/metrics |
| | config_audit | .env漂移/硬编码IP |
| **领域层** | healthcare | HIPAA/HL7 FHIR/脱敏 |

### 五大能力

```
全量扫描 ──── codespect-matrix --round 1
CI 门禁 ──── codespect-matrix --ci --json
风险评分 ──── codespect-matrix --risk-score
增量 diff ─── codespect-matrix --diff
基线对比 ──── codespect-matrix --baseline-diff
```

### 迭代收敛机制

```
本轮发现 P0/P1 ──→ 继续下一轮
本轮仅 P2/P3    ──→ 再跑一轮确认
连续 2 轮无问题 ──→ 收敛，输出最终报告
```

---

## 医疗领域专项

上海交通大学医学院背景，天生具备医疗领域基因：

| 检查项 | 说明 |
|---|---|
| PHI 隐私扫描 | 日志、print、异常、导出、API 中的患者信息泄露 |
| 医学数据校验 | 15类指标范围（血压60-260、血糖1-35、血氧60-100…） |
| 身份证/IPC格式 | 18位校验位 + ICD-10 编码格式验证 |
| ETL 数据完整性 | 行数校验、主键去重、外键孤儿、时间戳单调性 |
| 数据脱敏验证 | 姓名→假名、身份证→哈希、导出缺脱敏 |

---

## CI/CD 集成

```yaml
# .github/workflows/qa.yml
- name: codespect-matrix gate
  run: codespect-matrix --ci --json > qa-report.json
  # exit_code=0 放行，exit_code=1 拦截
```

<!--
    门禁规则：
    - critical > 0   → FAIL
    - high > 5       → FAIL
    - medium > 30    → FAIL
    - 否则            → PASS
-->

---

## 大模型支持

7 家厂商适配，未配置时自动降级为规则引擎模式（无需大模型也能完整校验）：

| 提供商 | 配置方式 |
|---|---|
| OpenAI (GPT-4o) | `LLM_PROVIDER=openai` |
| Anthropic (Claude) | `LLM_PROVIDER=anthropic` |
| Google (Gemini) | `LLM_PROVIDER=google` |
| 百度文心一言 | `LLM_PROVIDER=baidu` |
| 阿里通义千问 | `LLM_PROVIDER=tongyi` |
| 智谱 GLM | `LLM_PROVIDER=zhipu` |
| Hugging Face | `LLM_PROVIDER=huggingface` |

```bash
cp .env.example .env
# 填入你的 API Key
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxxx
```

---

## API 使用

```python
from codespect_matrix import QAService

qa = QAService(project_path="/path/to/project")

# 全量扫描（26 位专家全部运行）
result = qa.validate(round_number=1)

# CI 门禁
gate = qa.ci_check()
print(f"Exit: {gate['exit_code']} | Risk: {gate['risk_score']['risk_level']}")

# 风险评分（加权，可输出雷达图数据）
score = qa.compute_risk_score(result.issues_found)
print(score["risk_level"], score["by_severity"], score["by_expert"])

# 增量扫描（仅 git diff 变更文件）
diff = qa.validate_diff(target_branch="HEAD~1")

# 基线管理
qa.save_baseline()
delta = qa.diff_baseline()
print(f"Trend: {delta['delta']['trend']} | +{delta['delta']['new_issues']} -{delta['delta']['resolved_issues']}")

# LLM 驱动的智能报告
qa.generate_report(use_llm=True)

# 完整迭代周期（自动多轮直到收敛）
qa.run_full_cycle(max_rounds=10)
```

---

## 自定义扩展

```python
from codespect_matrix import BasePerspectiveExpert, ValidationResult

class MyExpert(BasePerspectiveExpert):
    def get_name(self):
        return "my_expert"
    
    def get_compatibility(self, profile):
        return 0.9 if profile.get("domain") == "医疗" else 0.2
    
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

| 参数 | 简写 | 说明 |
|---|---|---|
| `--path` | `-p` | 项目路径（默认当前目录） |
| `--round` | `-r` | 校验轮次 |
| `--full-cycle` | `-f` | 完整收敛周期 |
| `--analyze` | `-a` | 仅分析项目特征 |
| `--ci` | — | CI/CD 门禁模式 |
| `--json` | — | 输出 JSON 格式 |
| `--diff [TARGET]` | — | 增量扫描（默认 HEAD~1） |
| `--risk-score` | — | 风险评分 |
| `--baseline` | — | 保存基线 |
| `--baseline-diff` | — | 对比基线 |
| `--targeted` | — | 快速模式（仅 top-5 专家） |
| `--report` | `-o` | 生成质量报告 |
| `--output` | — | 报告输出文件路径 |

---

## 问题分级

| 等级 | 权重 | 说明 |
|------|------|------|
| critical (P0) | 100 | 服务不可启动 / PHI泄露 / 编译失败 |
| high (P1) | 50 | 安全漏洞 / 数据不完整 / HTTP无超时 |
| medium (P2) | 15 | 不符合最佳实践 / 缺少限流/分页 |
| low (P3) | 3 | 优化建议 |

---

## 项目结构

```
codespect-matrix/
├── .env.example              # 环境配置（7种LLM + Sentry + Redis）
├── iterative_qa.yaml         # 策略配置（26位专家 + CI阈值）
├── pyproject.toml            # 构建配置
├── requirements.txt          # 依赖清单
├── SKILL.md                  # 技能规范（Trae 市场）
├── skill.yaml                # 技能元数据
├── codespect_matrix/
│   ├── __init__.py
│   ├── cli.py                # CLI（12个子命令）
│   ├── core.py               # QAService + 5能力引擎
│   ├── scanner.py            # 项目特征扫描器
│   ├── models.py             # 数据模型
│   ├── llm_service.py        # 7家LLM适配层
│   └── perspectives/
│       └── __init__.py       # 26 位视角专家
```

---

## 免费 + 捐赠

codespect-matrix 完全免费。如果对你有帮助，欢迎：
- ⭐ **Star 这个项目**
- 💰 **GitHub Sponsors**: [sponsor/zhouliang-sjtu](https://github.com/sponsors/zhouliang-sjtu)
- 📢 **分享给更多开发者**

---

## 许可证

MIT License © 2026 周良 · 上海交通大学医学院

---

<p align="center">
  <sub>Built with ❤️ at Shanghai Jiao Tong University School of Medicine</sub>
</p>
