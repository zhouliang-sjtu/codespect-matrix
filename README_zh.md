# codespect-matrix — 中文说明

[English](README.md) · 中文

## 关于本项目

**codespect-matrix** 是一个基于大模型的**多智能体代码进化平台**。16 位专业 AI Agent 对项目进行**辩论式审查**，交叉验证后给出裁决，并追踪代码健康度变化趋势。

### 快速开始

```bash
# 源码安装
git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
cd codespect-matrix
pip install -e .

# 默认多智能体审查
codespect-matrix

# CI 门禁模式
codespect-matrix --ci --json

# 代码进化分析（健康评分 + 技术债务 + 架构 + 改进路线图）
codespect-matrix --evolve

# 保存进化基线用于趋势对比
codespect-matrix --evolve-baseline

# 完整收敛循环
codespect-matrix --max-rounds 10 --output report.md
```

### 核心特性

- **16 个专业 Agent 辩论式审查**：并行探查 → 交叉审查 → 辩论裁决 → 收敛终止
- **混合引擎**：安全/医疗/PHI/合规使用规则+LLM双引擎，其他使用纯LLM推理
- **双记忆系统**：项目级记忆（`.codespect_matrix_agent_memory.json`）+ 全局知识库（`~/.codespect_matrix_knowledge/`），跨项目经验积累
- **代码进化平台**：健康评分 · 技术债务分析 · 架构健康度 · 测试覆盖率 · 改进路线图
- **AI自主修复**：扫描 → 修复方案 → 用户确认 → 自动执行
- **CI/CD门禁**：critical=0 / high≤5 / medium≤30 阈值自动判定

### 16 个 Agent

| Agent | 引擎 | 职责 |
|---|---|---|
| security | 规则+LLM | 漏洞扫描、弱加密、密钥泄露 |
| healthcare | 规则+LLM | HIPAA合规、患者数据保护 |
| phi_protection | 规则+LLM | PHI检测、身份证泄露、数据脱敏 |
| compliance | 规则+LLM | 许可证合规、GDPR审计 |
| medical_data | 规则+LLM | ICD编码、血压/血氧校验 |
| developer | 纯LLM | 类型安全、错误处理、代码质量 |
| architect | 纯LLM | 循环依赖、模块耦合 |
| performance | 纯LLM | N+1查询、内存炸弹、阻塞I/O |
| devops | 纯LLM | 可观测性、健康检查、优雅停机 |
| testing | 纯LLM | 测试覆盖率、可测试性 |
| api | 纯LLM | REST规范、限流、认证 |
| dependency | 纯LLM | 依赖版本、CVE扫描 |
| concurrency | 纯LLM | 竞态条件、死锁、线程安全 |
| linter | 子进程+LLM | Ruff/mypy/flake8 + LLM解读 |
| datascience | 纯LLM | 统计建模、数据完整性、过拟合检测 |
| hardcode | 纯LLM | 硬编码值、魔法数字、跨文件重复 |

### 5 阶段审查流程

| 阶段 | 机制 |
|---|---|
| 0. 选择 | 项目特征 + 全局知识库 → 自动选择 5-8 个最相关 Agent |
| 1. 探查 | 所有 Agent 并行扫描（安全/医疗使用规则+LLM双引擎） |
| 2. 审查 | 每项发现由不同领域 Agent 交叉验证 |
| 3. 辩论 | 争议发现 → 挑战 → 辩护 → Orchestrator 裁决 |
| 4. 收敛 | 连续 2 轮无新发现 → 自动终止 |

### 代码进化仪表盘

```bash
codespect-matrix --evolve          # 完整进化分析
codespect-matrix --evolve-baseline # 保存为基线用于趋势对比
```

| 维度 | 说明 |
|---|---|
| **健康评分** | 0-100，由 Agent 发现加权计算（critical×100, high×50, ...） |
| **技术债务** | TODO/FIXME/HACK 密度 + 过大文件 + 注释比例 |
| **架构** | 导入图 → 耦合度、循环依赖、God模块检测 |
| **测试覆盖率** | pytest --cov 集成 + 回退文件计数 |
| **演变趋势** | 基线对比 → 改善 / 恶化 / 稳定 |
| **改进路线图** | P0-P2 优先级改进项 + 预估工时 |

### 自进化引擎

```bash
codespect-matrix --evolve-self     # 查看工具学到了什么
```

codespect-matrix 从每次跨项目 QA 闭环中持续学习：

| 阶段 | 说明 |
|---|---|
| 1. 扫描 | 运行 codespect-matrix → 发现问题 |
| 2. 修复 | 应用修复 → `record_qa_cycle()` 记录修复细节 |
| 3. 再扫描 | 验证健康分提升 → 追踪增量 |
| 4. 学习 | 更新模式置信度、调整 Agent 权重 |
| 5. 进化 | `SelfEvolver.evolve()` 剪枝低效模板，提升已验证模式到全局知识库 |

长期使用后，工具会越来越精准：减少误报、更快推荐修复方案、更智能选择 Agent。

### 医疗领域专项

| 检查项 | 说明 |
|---|---|
| PHI 隐私扫描 | 患者信息在日志、print、异常、导出中的泄露 |
| 医学数据校验 | 血压(60-260)、血氧(60-100)、ICD-10格式、身份证校验 |
| 数据脱敏验证 | 姓名→假名、身份证→哈希 |

---

### LLM 支持

支持 7 种大模型，未配置 LLM 时自动回落纯规则模式：

| 提供商 | 环境变量 |
|---|---|
| OpenAI (GPT-4o) | `LLM_PROVIDER=openai` |
| Anthropic (Claude) | `LLM_PROVIDER=anthropic` |
| Google (Gemini) | `LLM_PROVIDER=google` |
| 百度 (ERNIE) | `LLM_PROVIDER=baidu` |
| 阿里 (Qwen) | `LLM_PROVIDER=tongyi` |
| 智谱 (GLM) | `LLM_PROVIDER=zhipu` |
| Hugging Face | `LLM_PROVIDER=huggingface` |

---

### CLI 命令参考

| 参数 | 说明 |
|------|------|
| `--path, -p` | 项目路径（默认：当前目录） |
| `--max-rounds` | 最大审查轮数（默认：5） |
| `--ci` | CI/CD门禁模式 |
| `--json` | JSON输出 |
| `--evolve` | 代码进化分析 |
| `--evolve-baseline` | 保存进化基线 |
| `--evolve-self` | 自进化摘要 — 工具从历史 QA 中学到了什么 |
| `--fix-plan` | AI修复 — 第1步：生成方案 |
| `--fix-execute` | AI修复 — 第2步：执行 |
| `--fix-all` | 包括高风险修复（配合 `--fix-execute`） |
| `--output` | 报告输出路径 |

---

### Python API

```python
# 多智能体审查
from codespect_matrix.agents import AgentOrchestrator

orch = AgentOrchestrator(project_path="/path/to/project")
orch.initialize()
result = orch.run_full_cycle()
print(result["total_findings"], "issues found")

# 代码进化分析
from codespect_matrix.evolution import EvolutionReporter

reporter = EvolutionReporter(project_path="/path/to/project")
report = reporter.generate_full_report()
print(f"Health: {report['health']['health_score']}/100")
```

```python
# 自进化
from codespect_matrix.evolution import SelfEvolver

evolver = SelfEvolver()
evolver.record_qa_cycle(
    project_name="my-app",
    before_health=62.3,
    findings=[...],           # 来自 Agent 扫描
    fixes_applied=[...],      # 修复内容
    after_health=85.1,        # 再扫描结果
)
evolver.evolve()              # 剪枝低效模式，提升已验证模式
print(evolver.get_evolution_summary())
```

---

### 开发

```bash
pip install -e ".[dev]"
pytest tests/ -q                         # 运行测试
pytest tests/ --cov=codespect_matrix     # 含覆盖率
mypy codespect_matrix/                   # 类型检查
ruff check codespect_matrix/             # 代码检查
```

---

完整英文文档请查看 [README.md](README.md)

---

**版本**: 1.0.0 · **状态**: 稳定 — 生产就绪  
**测试**: 82 通过 · **覆盖率**: 59%  
**架构**: 多智能体 · 辩论审查 · 混合引擎 · 代码进化 · 自主进化
