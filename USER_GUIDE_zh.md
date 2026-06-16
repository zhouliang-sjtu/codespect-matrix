# codespect-matrix 用户手册

> **版本**: 1.0.0 | **最后更新**: 2026-06-16  
> 多智能体代码进化平台 — 16 位 AI Agent 辩论式审查 · 混合引擎 · 健康评分 · 自主修复

---

## 目录

1. [简介](#1-简介)
2. [安装](#2-安装)
   - [2.1 系统要求](#21-系统要求)
   - [2.2 从源码安装](#22-从源码安装)
   - [2.3 验证安装](#23-验证安装)
3. [配置](#3-配置)
   - [3.1 环境变量配置 (.env)](#31-环境变量配置-env)
   - [3.2 LLM 提供商配置详解](#32-llm-提供商配置详解)
   - [3.3 无 LLM 模式（纯规则引擎）](#33-无-llm-模式纯规则引擎)
   - [3.4 agent_config.yaml 运行参数](#34-agent_configyaml-运行参数)
4. [使用模式详解](#4-使用模式详解)
   - [4.1 多智能体审查模式（默认）](#41-多智能体审查模式默认)
   - [4.2 CI/CD 门禁模式](#42-cicd-门禁模式)
   - [4.3 代码进化分析](#43-代码进化分析)
   - [4.4 AI 自主修复](#44-ai-自主修复)
   - [4.5 自进化查看](#45-自进化查看)
5. [命令行参数参考](#5-命令行参数参考)
6. [Python API 使用](#6-python-api-使用)
   - [6.1 多智能体审查](#61-多智能体审查)
   - [6.2 代码进化分析](#62-代码进化分析)
   - [6.3 自进化引擎](#63-自进化引擎)
7. [输出解读](#7-输出解读)
   - [7.1 审查报告解读](#71-审查报告解读)
   - [7.2 进化仪表盘解读](#72-进化仪表盘解读)
   - [7.3 CI 门禁输出解读](#73-ci-门禁输出解读)
8. [高级主题](#8-高级主题)
   - [8.1 双记忆系统](#81-双记忆系统)
   - [8.2 自进化引擎详解](#82-自进化引擎详解)
   - [8.3 医疗领域专项检查](#83-医疗领域专项检查)
   - [8.4 16 个 Agent 角色说明](#84-16-个-agent-角色说明)
   - [8.5 严重度等级与权重](#85-严重度等级与权重)
9. [配置文件完整参考](#9-配置文件完整参考)
10. [常见问题](#10-常见问题)

---

## 1. 简介

**codespect-matrix** 不是一个普通的 Linter。它是一个**虚拟 QA 团队**——16 位专业化 AI Agent 对您的项目进行**辩论式代码审查**，交叉验证每一条问题发现，收敛为最终裁决，并追踪代码健康度变化趋势。它跨项目学习，每次扫描都变得更聪明。

### 核心能力

| 能力 | 说明 |
|------|------|
| 辩论式审查 | 16 个 Agent 并行探查 → 跨领域交叉审查 → 争议进入辩论 → Orchestrator 裁决 |
| 混合引擎 | 安全/医疗/PHI/合规使用规则+LLM 双引擎，其他使用纯 LLM 推理 |
| 双记忆系统 | 项目级记忆（假阳性过滤）+ 全局知识库（跨项目经验积累） |
| 代码进化 | 健康评分 · 技术债务 · 架构分析 · 测试覆盖率 · 改进路线图 |
| AI 自主修复 | 扫描 → 修复方案 → 用户确认 → 自动执行 → 再验证 |
| CI/CD 门禁 | critical=0 / high≤5 / medium≤30 阈值自动判定 |
| 医疗专项 | 内置 PHI/HIPAA/医学数据校验/数据脱敏 |

### 与传统 QA 工具对比

| 传统 QA | codespect-matrix |
|---------|------------------|
| 单一维度（Linter/Coverage） | 16 个 Agent 联合辩论审查 |
| 僵化规则，配置繁重 | AI Agent 自动适配项目特征 |
| 只报告问题，不提供修复 | 每条问题附带修复方案 + 自动修复 |
| 一次性扫描 | **收敛循环**——重复至无新发现 |
| 无 CI 集成 | `--ci` 退出码 + JSON，适配 CI/CD |
| 无法量化质量变化 | `--evolve` 健康仪表盘 + 趋势追踪 |
| 通用、无领域特化 | 内置 PHI/HIPAA/医疗数据专项 |

---

## 2. 安装

### 2.1 系统要求

| 项目 | 要求 |
|------|------|
| Python | 3.10、3.11 或 3.12 |
| 操作系统 | Windows / macOS / Linux |
| 磁盘空间 | ~200 MB（含依赖） |
| 可选：LLM API Key | 使用 LLM 功能时需配置（见 [3.2 节](#32-llm-提供商配置详解)） |

> **无需 GPU**。所有 AI 推理通过云 API 完成，本工具仅在本地运行编排逻辑。

### 2.2 从源码安装

```bash
# 1. 克隆仓库
git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
cd codespect-matrix

# 2. 安装（开发模式，推荐）
pip install -e .

# 3. 可选：安装额外依赖
pip install -e ".[dev]"       # 开发工具（ruff, mypy, pytest）
pip install -e ".[anthropic]"  # Anthropic Claude 支持
pip install -e ".[google]"     # Google Gemini 支持
pip install -e ".[baidu]"      # 百度 ERNIE 支持
pip install -e ".[tongyi]"     # 阿里通义千问支持
pip install -e ".[zhipu]"      # 智谱 GLM 支持
pip install -e ".[huggingface]" # HuggingFace 本地模型支持
```

> **提示**：安装 LLM 提供商对应的可选依赖后，需同时配置对应的 API Key（见 [3.2 节](#32-llm-提供商配置详解)）。

### 2.3 验证安装

```bash
# 检查命令行是否可用
codespect-matrix --help

# 在任意项目目录运行快速测试（无需 LLM）
codespect-matrix --path . --max-rounds 1 --json
```

如果输出 JSON 格式的扫描结果，说明安装成功。

---

## 3. 配置

### 3.1 环境变量配置 (.env)

在项目根目录（或任意代码项目的根目录）创建 `.env` 文件：

```bash
# 复制模板
cp .env.example .env
```

**.env 文件完整模板**：

```ini
# ==================== 大模型配置 ====================

# 模型提供商 (支持: openai, anthropic, google, baidu, tongyi, zhipu, huggingface)
# 如不配置此项，自动降级为纯规则引擎模式
LLM_PROVIDER=openai

# OpenAI 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1   # 支持自定义代理地址
OPENAI_MODEL=gpt-4o-mini                     # 推荐: gpt-4o 用于审查，gpt-4o-mini 用于轻量任务
OPENAI_TEMPERATURE=0.7                       # 生成类任务温度
OPENAI_MAX_TOKENS=4096

# Anthropic 配置
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Google Gemini 配置
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-pro

# 百度文心一言配置
BAIDU_API_KEY=your-baidu-api-key
BAIDU_SECRET_KEY=your-baidu-secret-key
BAIDU_MODEL=ERNIE-Bot-4.0

# 阿里云通义千问配置
TONGYI_API_KEY=your-tongyi-api-key
TONGYI_MODEL=qwen-plus

# 智谱 AI 配置
ZHIPU_API_KEY=your-zhipu-api-key
ZHIPU_MODEL=glm-4

# Hugging Face 配置
HUGGINGFACE_API_KEY=your-huggingface-api-key
HUGGINGFACE_MODEL=mistralai/Mistral-7B-v0.3

# ==================== 应用配置 ====================

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# 最大重试次数
MAX_RETRIES=3
```

### 3.2 LLM 提供商配置详解

codespect-matrix 支持 **7 种大模型提供商**，通过 `.env` 文件中的 `LLM_PROVIDER` 切换：

| 提供商 | LLM_PROVIDER 值 | 需要安装的额外依赖 | 推荐模型 |
|--------|----------------|-------------------|---------|
| OpenAI | `openai` | 无（内置） | `gpt-4o`（审查）/ `gpt-4o-mini`（轻量） |
| Anthropic | `anthropic` | `pip install -e ".[anthropic]"` | `claude-3-sonnet-20240229` |
| Google | `google` | `pip install -e ".[google]"` | `gemini-pro` |
| 百度 | `baidu` | `pip install -e ".[baidu]"` | `ERNIE-Bot-4.0` |
| 阿里 | `tongyi` | `pip install -e ".[tongyi]"` | `qwen-plus` |
| 智谱 | `zhipu` | `pip install -e ".[zhipu]"` | `glm-4` |
| HuggingFace | `huggingface` | `pip install -e ".[huggingface]"` | `mistralai/Mistral-7B-v0.3` |

**配置步骤（以 OpenAI 为例）**：

1. 在 `.env` 中设置 `LLM_PROVIDER=openai`
2. 设置 `OPENAI_API_KEY=sk-xxxx`
3. 可选：设置 `OPENAI_API_BASE` 使用自定义代理
4. 可选：设置 `OPENAI_MODEL` 选择模型版本

**使用自定义 API 代理**：

```ini
# 适用于使用第三方代理或 Azure OpenAI 的场景
OPENAI_API_BASE=https://your-proxy.com/v1
OPENAI_API_KEY=your-key
```

### 3.3 无 LLM 模式（纯规则引擎）

**codespect-matrix 可以在完全不配置 LLM 的情况下运行**。此时：

- **规则引擎 Agent**（SecurityAgent、HealthcareAgent、PHIAgent、ComplianceAgent、MedicalDataAgent）仍然正常工作，使用内置规则进行扫描
- **纯 LLM Agent**（DeveloperAgent、ArchitectAgent、PerformanceAgent 等）将被跳过
- 审查仍然有效，但发现的问题数量和深度可能低于 LLM 模式

**配置纯规则模式**：

只需不在 `.env` 中设置任何 LLM 相关配置即可。系统会自动检测并降级。

也可以在 `agent_config.yaml` 中明确设置：

```yaml
engine:
  llm_unavailable: rule_only   # 可选: rule_only | skip | error
```

### 3.4 agent_config.yaml 运行参数

项目根目录的 `agent_config.yaml` 控制运行时行为。你可以复制此文件到目标项目目录覆盖默认值。

```yaml
# Agent 选择策略
agent_selection:
  strategy: auto              # auto | profile_matching | fixed_list
  min_compatibility: 0.3      # profile_matching 策略的最小兼容度
  max_active: 8               # 每轮最多激活的 Agent 数量

# 探查阶段
inspection:
  max_context_tokens: 12000   # 发送给 LLM 的最大文件上下文 token 数
  timeout_per_agent: 120      # 每个 Agent 的超时时间（秒）
  retry_count: 2              # LLM 调用失败重试次数

# 交叉审查阶段
review:
  min_reviewers: 2            # 每条发现最少审查人数（来自不同领域）
  confirm_threshold: 0.75     # 确认阈值（高于此值为 confirmed）
  disagreement_threshold: 0.35 # 分歧阈值（超过此值进入辩论）

# 辩论阶段
debate:
  max_rounds: 3               # 单条发现的最大辩论轮数
  arbiter_threshold: 0.8      # 仲裁者置信度阈值
  round_timeout: 90           # 每轮辩论超时（秒）

# 收敛控制
convergence:
  max_rounds: 5               # 最大探查轮数
  stability_threshold: 2      # 连续无新发现轮数后自动终止

# 修复引擎
fix:
  auto_backup: true           # 修改前自动备份
  backup_dir: ".codespect_matrix_backups"
  require_confirmation: true  # 执行前需用户确认
  max_files_per_session: 20   # 单次修复最大文件数

# CI 门禁阈值
ci_gate:
  max_critical: 0
  max_high: 5
  max_medium: 30

# 引擎回退
engine:
  llm_unavailable: rule_only
  analysis_temperature: 0.2
  default_model: "gpt-4o"
```

---

## 4. 使用模式详解

codespect-matrix 提供 **5 种主要使用模式**，通过不同的命令行参数触发。

### 4.1 多智能体审查模式（默认）

最完整的审查模式，执行全部 5 个阶段：

1. **Agent 选择** — 根据项目特征自动选择 5-8 个最匹配的 Agent
2. **并行探查** — 所有选中的 Agent 同时扫描源代码
3. **交叉审查** — 每条发现由不同领域 Agent 交叉验证
4. **辩论裁决** — 争议发现进入辩论，Orchestrator 最终裁决
5. **收敛循环** — 重复探查直到连续 2 轮无新发现

#### 基本用法

```bash
# 在当前目录进行审查
codespect-matrix

# 指定目标项目路径
codespect-matrix --path /home/user/my-project

# 使用相对路径
codespect-matrix -p ../my-python-app
```

#### 控制审查轮数

```bash
# 快速扫描（1 轮）
codespect-matrix --max-rounds 1

# 深度审查（10 轮）
codespect-matrix --max-rounds 10
```

> **提示**：收敛机制会自动终止。设置较大的 `--max-rounds` 只是设置上限，当连续 2 轮无新发现时审查会自动结束。

#### 输出格式

```bash
# JSON 格式输出（便于程序处理）
codespect-matrix --json

# 保存报告到文件
codespect-matrix --output report.md

# 同时输出 JSON 并保存文件
codespect-matrix --json --output report.json
```

#### 审查输出示例

```
======================================================================
  codespect-matrix — 16-Agent Code Evolution Platform
  Review · Debate · Converge · Evolve
======================================================================

  project: Backend
  domain: 医疗
  scale: medium
  7 agents active:
    [security       ] security — Vulnerability scanning, crypto strength audit...
    [healthcare     ] healthcare — HIPAA compliance, patient data protection
    [code_quality   ] developer — Code quality, type safety, error handling...
    [architecture   ] architect — Circular dependency, module coupling...
    [performance    ] performance — N+1 queries, memory bombs, blocking I/O...
    [testing        ] testing — Test coverage, testability...
    [api            ] api — REST conventions, rate limiting, auth...

  starting review...

  === ROUND 1 ===
  Inspecting... 7 agents scanned, 23 findings
  Reviewing... cross-validated by different-domain agents
  Ruling: 15 confirmed, 5 rejected, 3 disputed

  === ROUND 2 ===
  Debate closed: 3 disputed → 2 confirmed, 1 rejected
  Inspecting... 7 agents scanned, 2 new findings
  Converged: 2 consecutive rounds with no new findings

  ============================================================
  REVIEW SUMMARY
  ============================================================
  Total findings:    25
  Confirmed:         17
  Rejected:          6
  Adjusted:          2
  Rounds:            2
  Converged:         yes

  Critical: 1
    - phi_protection_patient_id_leak: Patient ID found in log output
      File: src/api/patient_export.py:42
      Fix: Use masked_patient_id() before logging

  High: 3
    - security_eval_injection: eval() with user-controlled input
      File: src/utils/dynamic_query.py:18
      Fix: Use ast.literal_eval() or safe parser
    ...
```

### 4.2 CI/CD 门禁模式

用于在 CI/CD 流水线中集成代码审查。根据预定义阈值判断代码质量是否通过门禁。

#### 默认阈值

| 级别 | 最大允许数量 |
|------|------------|
| Critical (P0) | 0 |
| High (P1) | 5 |
| Medium (P2) | 30 |

阈值可在 `agent_config.yaml` 的 `ci_gate` 节中自定义。

#### 基本用法

```bash
# CI 门禁检查（以退出码表示结果）
codespect-matrix --ci

# 输出 JSON 格式（CI 工具友好）
codespect-matrix --ci --json > qa-report.json
```

#### 退出码

| 退出码 | 含义 |
|--------|------|
| `0` | 通过 — 所有严重度均未超过阈值 |
| `1` | 未通过 — 至少一个严重度超过阈值 |

#### CI 输出示例

```
============================================================
CI Gate Check — FAIL
============================================================
severities: {'critical': 0, 'high': 6, 'medium': 12}
confirmed: 18
rejected: 7
gate: FAIL
```

#### GitHub Actions 集成示例

```yaml
name: Code Quality Gate

on:
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install codespect-matrix
        run: |
          git clone https://github.com/zhouliang-sjtu/codespect-matrix.git
          cd codespect-matrix && pip install -e .

      - name: Run Quality Gate
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          cd ${{ github.workspace }}/your-project
          codespect-matrix --ci --json --path . > codespect-report.json

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: codespect-report
          path: codespect-report.json
```

#### GitLab CI 集成示例

```yaml
# .gitlab-ci.yml
quality-gate:
  image: python:3.11
  stage: test
  before_script:
    - git clone https://github.com/zhouliang-sjtu/codespect-matrix.git /tmp/codespect
    - cd /tmp/codespect && pip install -e .
  script:
    - cd $CI_PROJECT_DIR
    - codespect-matrix --ci --json --path . > codespect-report.json
  artifacts:
    when: always
    paths:
      - codespect-report.json
```

### 4.3 代码进化分析

对项目进行全面的代码进化分析，生成健康仪表盘、技术债务报告、架构分析和改进路线图。

#### 基本用法

```bash
# 完整进化分析（健康评分 + 技术债务 + 架构 + 路线图）
codespect-matrix --evolve

# 保存进化基线（用于后续趋势对比）
codespect-matrix --evolve-baseline

# 对比查看趋势
codespect-matrix --evolve    # 如果有基线文件，自动对比

# JSON 格式输出
codespect-matrix --evolve --json
```

#### 进化仪表盘输出解读

```
----------------------------------------------------------------------
PROJECT HEALTH DASHBOARD
----------------------------------------------------------------------
  Overall Health       OK [########################------]  80.5%
    Code Quality       OK [########################------]  78.0%
    Architecture       OK [#########################-----]  82.3%
    Debt Freedom       OK [########################------]  79.0%
    Test Coverage      ~~ [##############----------------]  45.0%

  CODE QUALITY [GOOD]
    score: 78.0/100
    high: 3
    medium: 12
    low: 5

  TECHNICAL DEBT [MODERATE]
    index: 35/100
    markers: 8
      [TODO] Refactor patient data export module...
      [FIXME] Race condition when concurrent write...
    large files: 2
      src/api/handler.py (1234 lines)
      src/models/database.py (892 lines)

  ARCHITECTURE [CLEAN]
    health: 82.3/100
    modules: 24
    cycles: 0
    god modules: 1
      src/api/handler.py (1234 lines, fan-out: 18)

  TEST COVERAGE [MODERATE]
    coverage: 45.0%
    lines: 890/1978

  ------------------------------------------------------------
  IMPROVEMENT ROADMAP
  ------------------------------------------------------------
  [P1] technical_debt
       Resolve 8 TODO/FIXME/HACK markers
       reason: Debt index 35/100
       effort: 4h estimated

  [P1] architecture
       Refactor 1 God modules
       reason: src/api/handler.py
       effort: 2-4h per module

  [P2] technical_debt
       Split 2 oversized files (>500 lines)
       reason: Large files: src/api/handler.py, src/models/database.py
       effort: 4h estimated

  [P2] testing
       Increase test coverage to 50%+
       reason: Current coverage: 45.0%
       effort: depends on project size
```

#### 进化趋势对比

首次运行 `--evolve-baseline` 后，后续运行 `--evolve` 会自动对比：

```
  Evolution Trend — IMPROVING
    Health:  78.0 → 82.5 (+4.5)
    Debt:    35 → 28 (-7)
    Findings: 25 → 18 (-7)
```

### 4.4 AI 自主修复

两步式 AI 修复流程：先生成修复方案供审查，确认后再执行。

#### 第一步：生成修复方案

```bash
# 扫描项目并生成修复方案（预览，不修改代码）
codespect-matrix --fix-plan
```

输出示例：

```
  ============================================================
  codespect-matrix — AI Autonomous Fix: Generate Plan
  ============================================================

  Health score (before): 62.0/100
  Confirmed issues:     17
  Auto-fixable:         12
  Needs manual review:  5

  Auto-fixable issues:
  ----------------------------------------------------
  [H] security_eval_injection
       eval() with user-controlled input in dynamic_query
       src/utils/dynamic_query.py:18
       fix: Replace eval() with ast.literal_eval() for safe parsing

  [M] developer_missing_timeout
       HTTP request without timeout parameter
       src/api/client.py:45
       fix: Add timeout=30 parameter to requests.get() call
  ...

  To apply auto-fixes:   codespect-matrix --fix-execute
  To apply ALL fixes:    codespect-matrix --fix-execute --fix-all
  (backups saved to .codespect_matrix_backups/)
```

#### 第二步：执行修复

```bash
# 仅执行安全修复（can_auto_fix=true 的修复项）
codespect-matrix --fix-execute

# 执行所有修复（包括高风险项）
codespect-matrix --fix-execute --fix-all
```

执行后会自动：
1. **备份原文件** → `.codespect_matrix_backups/` 目录
2. **逐项应用修复** → LLM 生成精确的 old_str/new_str 补丁
3. **重新扫描验证** → 确认健康分是否提升
4. **记录到自进化引擎** → 供后续学习

输出示例：

```
  Health before fix:  62.0/100
  Issues to address:  17

  Fix results:
    Applied:  12
    Failed:   0

  Files modified:
    - src/utils/dynamic_query.py
    - src/api/client.py
    ...

  Backups saved to: .codespect_matrix_backups/

  Re-scanning to verify...
  Health after fix:   78.5/100
  Improvement:        +16.5
  SelfEvolver:        cycle recorded for future learning
```

> **安全提示**：修复引擎会自动备份被修改的文件到 `.codespect_matrix_backups/`。如果修复结果不理想，可以从备份恢复。

#### 回滚修复

```bash
# 从备份目录恢复所有被修改的文件
cp -r .codespect_matrix_backups/* .
```

### 4.5 自进化查看

查看工具从历史 QA 周期中学到了什么。

```bash
codespect-matrix --evolve-self
```

输出示例：

```
  ============================================================
  codespect-matrix — Self-Evolution Summary
  ============================================================

  Generation:        3
  QA Cycles:         47
  Projects Helped:   8
  Avg Health Gain:   +15.3%
  Patterns Learned:  23

  Top Agents:
    1. security (accuracy: 92%)
    2. developer (accuracy: 88%)
    3. phi_protection (accuracy: 95%)

  Fix Confidence by Issue Type:
    eval_injection          [####################] 95% (12 attempts)
    missing_timeout         [################    ] 80% (8 attempts)
    hardcoded_secret        [####################] 100% (5 attempts)
    ...
```

---

## 5. 命令行参数参考

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--path` | `-p` | string | `.` | 项目路径（绝对或相对路径） |
| `--max-rounds` | — | int | `5` | 最大审查轮数 |
| `--ci` | — | flag | — | CI/CD 门禁模式（退出码表示结果） |
| `--json` | — | flag | — | 输出 JSON 格式 |
| `--output` | — | string | — | 报告输出文件路径 |
| `--evolve` | — | flag | — | 代码进化分析（健康仪表盘 + 路线图） |
| `--evolve-baseline` | — | flag | — | 保存进化基线（用于趋势对比） |
| `--evolve-self` | — | flag | — | 自进化摘要 — 工具从历史学到了什么 |
| `--fix-plan` | — | flag | — | AI 修复第 1 步：生成修复方案 |
| `--fix-execute` | — | flag | — | AI 修复第 2 步：执行修复 |
| `--fix-all` | — | flag | — | 配合 `--fix-execute` 执行包括高风险的所有修复 |

### 常用命令组合

```bash
# === 日常审查 ===
codespect-matrix                                              # 默认审查
codespect-matrix -p /path/to/project --max-rounds 3           # 目标项目 3 轮审查
codespect-matrix --json --output report.json                  # JSON 输出并保存

# === CI/CD ===
codespect-matrix --ci --json                                  # CI 门禁
codespect-matrix --ci --json > qa-report.json                 # CI 门禁 + 保存报告

# === 进化分析 ===
codespect-matrix --evolve                                     # 健康仪表盘
codespect-matrix --evolve-baseline                            # 保存基线
codespect-matrix --evolve --evolve-baseline                   # 分析并保存基线

# === AI 修复 ===
codespect-matrix --fix-plan                                   # 生成方案
codespect-matrix --fix-execute                                # 执行安全修复
codespect-matrix --fix-execute --fix-all                      # 执行全部修复

# === 学习反馈 ===
codespect-matrix --evolve-self                                # 查看工具进化状态
codespect-matrix --evolve-self --json                         # JSON 格式进化状态
```

---

## 6. Python API 使用

如果需要在 Python 脚本中集成 codespect-matrix，可以使用 Python API。

### 6.1 多智能体审查

```python
from codespect_matrix.agents import AgentOrchestrator

# 初始化编排器
orch = AgentOrchestrator(project_path="/path/to/project")

# 初始化：分析项目 + 选择 Agent
orch.initialize()

# 运行完整审查周期
result = orch.run_full_cycle(max_rounds=5)

# 查看结果
print(f"Total findings: {result['total_findings']}")
print(f"Confirmed: {len(result['confirmed_issues'])}")
print(f"Rejected: {len(result['rejected_issues'])}")
print(f"Converged: {result['converged']}")

# 遍历已确认的问题
for issue in result['confirmed_issues']:
    print(f"[{issue['severity']}] {issue['check_name']}: {issue['message']}")

# 生成可读报告
report = orch.generate_report(result)
print(report)
```

### 6.2 代码进化分析

```python
from codespect_matrix.evolution import (
    EvolutionReporter,
    EvolutionBaseline,
    HealthScorer,
    TechDebtAnalyzer,
    ArchitectureAnalyzer,
    TestCoverageEstimator,
)

project_path = "/path/to/project"

# 方式 1：使用 EvolutionReporter 生成完整报告
reporter = EvolutionReporter(project_path)

# 如果你有 Agent 审查的结果
findings = [
    {"check_name": "security_eval", "severity": "critical", "message": "eval() injection"},
    {"check_name": "developer_timeout", "severity": "high", "message": "missing timeout"},
]

report = reporter.full_report(agent_findings=findings)
print(f"Health Score: {report['health']['health_score']}/100")
print(f"Overall: {report['overall_score']}/100 ({report['overall_level']})")
print(f"Technical Debt: {report['technical_debt']['debt_index']}/100")
print(f"Architecture: {report['architecture']['architecture_health']}/100")

# 方式 2：独立使用各分析器
health = HealthScorer().compute(findings)
debt = TechDebtAnalyzer().analyze(project_path)
arch = ArchitectureAnalyzer().analyze(project_path)
coverage = TestCoverageEstimator().estimate(project_path)

# 保存和加载基线
baseline = EvolutionBaseline(project_path)
baseline.save(report)            # 保存当前状态为基线

# 之后可以加载对比
previous = baseline.load()
if previous:
    delta = baseline.diff(report)  # 当前 vs 基线
    print(f"Trend: {delta['trend']}")
    print(f"Health delta: {delta['health_delta']:+.1f}")
```

### 6.3 自进化引擎

```python
from codespect_matrix.evolution import SelfEvolver

evolver = SelfEvolver()

# 记录一次 QA 闭环
evolver.record_qa_cycle(
    project_name="my-app",
    before_health=62.3,
    findings=[
        {"check_name": "security_eval", "severity": "critical", "message": "eval() used"},
        {"check_name": "developer_timeout", "severity": "high", "message": "no timeout"},
    ],
    fixes_applied=[
        {"check_name": "security_eval", "success": True},
        {"check_name": "developer_timeout", "success": True},
    ],
    after_health=85.1,
    fix_details=[
        {
            "check_name": "security_eval",
            "reasoning": "Replaced eval() with ast.literal_eval()",
            "old_code": "return eval(user_input)",
            "new_code": "return ast.literal_eval(user_input)",
        },
    ],
)

# 触发进化：剪枝低效模式，提升已验证模式
evolver.evolve()

# 查看进化摘要
summary = evolver.get_evolution_summary()
print(f"Generation: {summary['generation']}")
print(f"Total Cycles: {summary['total_cycles']}")
print(f"Avg Health Gain: {summary['average_health_improvement']}%")
```

---

## 7. 输出解读

### 7.1 审查报告解读

多智能体审查输出包含以下关键信息：

| 区域 | 说明 |
|------|------|
| **Project Info** | 项目类型、领域、规模、活跃 Agent 列表 |
| **Round Results** | 每轮的探查发现数、确认数、拒绝数 |
| **Review Summary** | 总计发现、确认、拒绝、调整数 |
| **Issue Detail** | 每条已确认问题的严重度、描述、文件位置、修复建议 |

**严重度颜色标记**：
- `[C]` Critical (P0) — 必须立即修复，可能导致崩溃/数据泄露
- `[H]` High (P1) — 应尽快修复，安全漏洞/数据丢失
- `[M]` Medium (P2) — 建议修复，最佳实践违规
- `[L]` Low (P3) — 优化建议

### 7.2 进化仪表盘解读

| 指标 | 范围 | 优秀 | 良好 | 一般 | 较差 | 危险 |
|------|------|------|------|------|------|------|
| Overall Health | 0-100 | ≥85 | ≥70 | ≥50 | ≥30 | <30 |
| Code Quality | 0-100 | ≥90 | ≥70 | ≥50 | ≥30 | <30 |
| Architecture | 0-100 | ≥80 | ≥60 | ≥40 | — | <40 |
| Debt Freedom | 0-100 | ≥80 | ≥70 | ≥50 | — | <50 |
| Test Coverage | 0-100% | ≥80% | ≥50% | >0% | — | 0% |

**技术债务指数 (Debt Index)**：
- 0-19: 低 — 代码清洁
- 20-49: 中等 — 有一些标记需要处理
- 50-79: 高 — 积累显著，建议优先处理
- 80-100: 危险 — 严重影响可维护性

### 7.3 CI 门禁输出解读

```json
{
  "exit_code": 1,
  "severities": {
    "critical": 0,
    "high": 6,
    "medium": 12
  },
  "total_findings": 25,
  "confirmed": 18,
  "rejected": 7,
  "converged": false,
  "timestamp": "2026-06-16T10:30:00Z"
}
```

| 字段 | 说明 |
|------|------|
| `exit_code` | 0=通过, 1=未通过 |
| `severities.critical` | Critical 级别问题数（阈值: 0） |
| `severities.high` | High 级别问题数（阈值: ≤5） |
| `severities.medium` | Medium 级别问题数（阈值: ≤30） |
| `total_findings` | 所有 Agent 发现总数（含重复） |
| `confirmed` | 经交叉审查确认的问题数 |
| `rejected` | 经交叉审查被拒绝的问题数 |
| `converged` | 是否在 1 轮内收敛 |
| `timestamp` | 审查时间戳 |

---

## 8. 高级主题

### 8.1 双记忆系统

codespect-matrix 拥有两层记忆系统，通过跨项目和跨会话的知识积累持续提升审查质量。

#### 项目级记忆 (Project Memory)

存储在每个项目根目录的 `.codespect_matrix_agent_memory.json` 中：

- **假阳性记录**：已确认不是问题的问题，后续扫描自动过滤
- **扫描历史**：历次审查的发现数和健康分变化
- **收敛追踪**：记录那些已经通过多轮辩论确认的结论

```json
// .codespect_matrix_agent_memory.json 示例结构
{
  "false_positives": [
    {"check_name": "security_eval_injection", "message": "...", "confirmed_fp": true}
  ],
  "scan_history": [
    {"timestamp": "2026-06-15", "findings": 25, "confirmed": 17}
  ],
  "convergence_records": {}
}
```

#### 全局知识库 (Global Knowledge Base)

存储在 `~/.codespect_matrix_knowledge/` 目录，跨所有项目共享：

- **跨项目假阳性库**：某些检查项在你的所有项目中都会触发误报
- **Agent 推荐权重**：基于历史效果，同类项目自动推荐最有效的 Agent
- **修复模式库**：成功修复的代码模式，供后续修复参考
- **自进化数据**：QA 闭环中积累的经验（见 [8.2 节](#82-自进化引擎详解)）

```bash
# 查看全局知识库位置
ls ~/.codespect_matrix_knowledge/

# 手动清除全局知识库（重置学习状态）
rm -rf ~/.codespect_matrix_knowledge/
```

### 8.2 自进化引擎详解

SelfEvolver 是 codespect-matrix 的核心差异化功能，让工具从每次 QA 闭环中持续学习。

#### 进化闭环

```
   ┌──────────────────────────────────────────────────┐
   │                                                  │
   ▼                                                  │
┌──────┐   ┌──────┐   ┌──────────┐   ┌──────┐   ┌──────┐
│Scan  │──▶│Fix   │──▶│Re-scan   │──▶│Learn │──▶│Evolve│
│      │   │Apply │   │Verify    │   │Update│   │Prune │
└──────┘   └──────┘   └──────────┘   └──────┘   └──────┘
                                                │
                                                ▼
                                         ┌──────────┐
                                         │Global KB │
                                         │Updated   │
                                         └──────────┘
```

#### 进化过程

| 阶段 | 操作 | 效果 |
|------|------|------|
| Scan | 运行 codespect-matrix 审查 | 发现 n 个问题 |
| Fix | 应用修复（手动或 `--fix-execute`） | 修复 m 个问题 |
| Re-scan | 再次审查验证 | 健康分从 A → B |
| Learn | record_qa_cycle() 记录 | 更新修复模式置信度 |
| Evolve | evolve() 剪枝优化 | 低效模板降权，高效模板提升到全局知识库 |

#### 长期效果

使用 codespect-matrix 审查、修复、再审查的项目越多，工具会：

- **减少误报**：自动学习哪些模式在你的代码库中不是问题
- **更快定位**：根据历史效果自动推荐最合适的 Agent
- **更准修复**：成功修复过的模式，下次直接推荐高置信度修复方案
- **智能选型**：新项目 根据相似项目经验自动选择最佳 Agent 组合

### 8.3 医疗领域专项检查

codespect-matrix 内置了针对医疗健康领域的专项检查能力：

| 检查项 | 触发条件 | 检测内容 |
|--------|---------|---------|
| **PHI 隐私扫描** | 项目领域识别为"医疗" | 患者信息在日志、print、异常、导出、API 响应中的泄露 |
| **医学数据校验** | 同上 | 血压范围(60-260)、血氧范围(60-100)、ICD-10 编码格式、中国身份证校验和 |
| **数据脱敏验证** | 同上 | 姓名→假名、身份证→哈希、导出数据未脱敏 |
| **HIPAA 合规** | 同上 | 审计日志缺失、数据传输未加密、访问控制不足 |

这些检查由专门的 Agent 执行：
- **PHIAgent** (`phi_protection`): PHI/PII 数据泄露检测
- **HealthcareAgent** (`healthcare`): HIPAA 合规审计
- **MedicalDataAgent** (`medical_data`): 医学生理数据格式和范围校验
- **ComplianceAgent** (`compliance`): 许可证合规、GDPR 审计

### 8.4 16 个 Agent 角色说明

| Agent ID | 名称 | 引擎类型 | 职责范围 |
|----------|------|---------|---------|
| `security` | SecurityAgent | 规则+LLM | 漏洞扫描、弱加密检测、硬编码密钥、不安全反序列化 |
| `healthcare` | HealthcareAgent | 规则+LLM | HIPAA 合规、患者数据保护、访问控制审计 |
| `phi_protection` | PHIAgent | 规则+LLM | PHI/PII 检测、身份证号码泄露、日志数据脱敏 |
| `compliance` | ComplianceAgent | 规则+LLM | 许可证合规、GDPR 审计、审计日志完整性 |
| `medical_data` | MedicalDataAgent | 规则+LLM | ICD-10 编码、血压/血氧范围、中国身份证校验 |
| `developer` | DeveloperAgent | 纯LLM | 类型安全、错误处理、函数复杂度、命名规范 |
| `architect` | ArchitectAgent | 纯LLM | 循环依赖检测、模块耦合分析、God 模块识别 |
| `performance` | PerformanceAgent | 纯LLM | N+1 查询、内存泄漏、阻塞 I/O、大对象分配 |
| `devops` | DevopsAgent | 纯LLM | 可观测性、健康检查、优雅停机、资源限制 |
| `testing` | TestingAgent | 纯LLM | 测试覆盖率、可测试性、Mock 使用、断言质量 |
| `api` | APIAgent | 纯LLM | REST 规范、限流策略、认证授权、错误响应格式 |
| `dependency` | DependencyAgent | 纯LLM | 依赖版本检查、CVE 扫描、过时包检测 |
| `concurrency` | ConcurrencyAgent | 纯LLM | 竞态条件、死锁检测、线程安全、异步编程 |
| `linter` | LinterAgent | 子进程+LLM | Ruff/mypy/flake8 运行 + LLM 解读结果 |
| `datascience` | DataScienceAgent | 纯LLM | 统计建模正确性、数据完整性、过拟合检测 |
| `hardcode` | HardcodeAgent | 纯LLM | 硬编码值识别、魔法数字检测、跨文件重复值 |

### 8.5 严重度等级与权重

在健康评分计算中，不同严重度使用不同权重：

| 级别 | 标签 | 权重 | 说明 | 示例 |
|------|------|------|------|------|
| Critical | P0 | ×100 | 服务崩溃 / PHI 泄露 / 编译失败 | `eval()` 注入、患者 ID 明文日志 |
| High | P1 | ×50 | 安全漏洞 / 数据丢失 / 缺少超时 | 硬编码密钥、HTTP 请求无 timeout |
| Medium | P2 | ×15 | 最佳实践违规 / 缺少限流 | 缺少 rate limiting、TODO 堆积 |
| Low | P3 | ×3 | 优化建议 | 命名改进、代码风格 |

**健康评分公式**：

```
raw_score = Σ(severity_weight × count_per_severity)
max_score = Σ(severity_weight × 10)    # 基准：每类 10 个
health = max(0, 100 - (raw_score / max_score) × 100)
```

---

## 9. 配置文件完整参考

### agent_config.yaml 默认值

```yaml
# ─── Agent 选择 ────────────────────────────────
agent_selection:
  strategy: auto
  min_compatibility: 0.3
  max_active: 8

# ─── 探查阶段 ──────────────────────────────────
inspection:
  max_context_tokens: 12000
  timeout_per_agent: 120
  retry_count: 2

# ─── 交叉审查阶段 ──────────────────────────────
review:
  min_reviewers: 2
  confirm_threshold: 0.75
  disagreement_threshold: 0.35

# ─── 辩论阶段 ──────────────────────────────────
debate:
  max_rounds: 3
  arbiter_threshold: 0.8
  round_timeout: 90

# ─── 收敛 ──────────────────────────────────────
convergence:
  max_rounds: 5
  stability_threshold: 2

# ─── 修复引擎 ──────────────────────────────────
fix:
  auto_backup: true
  backup_dir: ".codespect_matrix_backups"
  require_confirmation: true
  max_files_per_session: 20

# ─── 记忆系统 ──────────────────────────────────
memory:
  project_memory: true
  project_memory_file: ".codespect_matrix_agent_memory.json"
  global_knowledge: true
  global_kb_dir: "~/.codespect_matrix_knowledge/"

# ─── CI 门禁 ───────────────────────────────────
ci_gate:
  max_critical: 0
  max_high: 5
  max_medium: 30

# ─── 引擎回退 ──────────────────────────────────
engine:
  llm_unavailable: rule_only
  analysis_temperature: 0.2
  default_model: "gpt-4o"
```

### 项目生成的文件

运行 codespect-matrix 后，项目目录中会生成以下文件：

| 文件 | 用途 | 建议 |
|------|------|------|
| `.codespect_matrix_agent_memory.json` | 项目级记忆 | 提交到 Git |
| `.codespect_matrix_backups/` | 修复前的备份 | 修复验证后删除 |
| `.codespect_matrix_evolution_baseline.json` | 进化基线 | 提交到 Git |
| `~/.codespect_matrix_knowledge/` | 全局知识库 | 不提交，保留在本地 |

---

## 10. 常见问题

### Q1: 未配置 LLM 能使用吗？

**可以。** codespect-matrix 支持纯规则引擎模式。在无 LLM 配置时：
- 规则引擎 Agent（security, healthcare, phi_protection, compliance, medical_data）正常工作
- 纯 LLM Agent 被自动跳过
- 审查范围缩小，但仍有效

### Q2: 支持哪些编程语言？

当前主要优化支持 **Python** 项目。其他语言的项目可以运行进化分析（技术债务、架构分析仅支持 Python），但多智能体审查中的规则引擎 Agent 可能无法正确解析。

### Q3: LLM 调用费用高吗？

- 使用 `gpt-4o-mini` 审查一个中等规模项目（~5000行代码），约消耗 **5-15K tokens**，费用很低
- 使用 `gpt-4o` 进行全面审查，约消耗 **15-40K tokens**
- 建议日常使用 `gpt-4o-mini`，重要审查使用 `gpt-4o`

### Q4: 审查需要多长时间？

- 小型项目（<1000行）：**约 10-30 秒**
- 中型项目（1000-10000行）：**约 30-120 秒**
- 大型项目（>10000行）：**约 2-5 分钟**
- 时间主要受 LLM API 响应速度影响

### Q5: 如何只运行特定 Agent？

目前 Agent 是自动选择的。如需控制，可以：
1. 在 `agent_config.yaml` 中设置 `agent_selection.max_active` 限制数量
2. 或使用 Python API 手动指定：

```python
from codespect_matrix.agents import AgentOrchestrator

orch = AgentOrchestrator(project_path=".")
orch._register_all_agents()

# 手动选择 Agent
orch.active_agents = ["security", "developer", "linter"]
orch.run_full_cycle()
```

### Q6: 修复功能安全吗？

修复引擎设计为安全优先：

1. **自动备份**：每个被修改的文件先备份到 `.codespect_matrix_backups/`
2. **用户确认**：默认需要用户先查看 `--fix-plan` 再 `--fix-execute`
3. **安全修复优先**：标记为 `can_auto_fix=true` 的修复项（如添加超时参数、替换安全函数）
4. **模糊匹配**：LLM 生成的补丁如果精确匹配失败，会尝试上下文模糊匹配
5. **可回滚**：从备份目录直接恢复

### Q7: 进化基线应该何时更新？

建议在以下时机更新：

- 每次发版后：`codespect-matrix --evolve-baseline`
- 重大重构前/后：保存重构前基线，重构后对比
- 定期（如每月）：追踪项目健康度趋势

### Q8: 如何在多项目中使用？

```bash
# 每个项目独立使用
cd /path/to/project-a
codespect-matrix --evolve

cd /path/to/project-b
codespect-matrix --evolve

# Python API 批量处理
import os
from codespect_matrix.agents import AgentOrchestrator

projects = ["/path/to/a", "/path/to/b", "/path/to/c"]
for p in projects:
    orch = AgentOrchestrator(project_path=p)
    orch.initialize()
    result = orch.run_full_cycle(max_rounds=3)
    print(f"{os.path.basename(p)}: {len(result['confirmed_issues'])} issues")
```

### Q9: 什么是收敛？为什么重要？

收敛是指连续 2 轮探查没有发现新问题。这意味着在当前 Agent 配置下，所有可发现的问题都已经暴露。收敛机制确保：
- 不会无限循环扫描
- 审查有明确的终止条件
- 结果具有完整性（当前视角下）

### Q10: 可以自定义规则吗？

内置 Agent 使用预定义的检查逻辑（规则引擎）和 LLM 提示词（LLM Agent）。如果需要自定义：

1. **调整阈值**：修改 `agent_config.yaml` 中的审查/辩论参数
2. **添加假阳性过滤**：`.codespect_matrix_agent_memory.json` 中标记已知误报
3. **扩展 Agent**：通过 Python API 注册自定义 Agent（需要开发）

---

## 附录：项目文件结构

```
codespect-matrix/
├── codespect_matrix/            # 核心代码
│   ├── agents/                  # Agent 系统
│   │   ├── base.py              # Agent 基类和数据类型
│   │   ├── rule_agents.py       # 规则+LLM 混合 Agent（安全/医疗/PHI）
│   │   ├── llm_agents.py        # 纯 LLM Agent（开发者/架构/性能等）
│   │   ├── orchestrator.py      # 编排器 — 多Agent协调、审查流程
│   │   ├── bus.py               # Agent 间通信总线
│   │   └── memory.py            # 双记忆系统
│   ├── cli.py                   # 命令行入口
│   ├── core.py                  # 核心服务
│   ├── scanner.py               # 项目特征扫描器
│   ├── llm_service.py           # LLM 服务封装（7种提供商）
│   ├── fix_engine.py            # AI 修复引擎
│   ├── evolution.py             # 进化引擎（健康评分/技术债务/架构/自进化）
│   └── models.py                # 数据模型
├── locales/                     # 国际化
│   ├── zh/messages.json         # 中文消息
│   └── en/messages.json         # 英文消息
├── tests/                       # 测试
├── agent_config.yaml            # Agent 运行配置（默认值）
├── .env.example                 # 环境变量模板
├── pyproject.toml               # 项目元数据和依赖
├── README.md                    # 项目简介（英文）
├── README_zh.md                 # 项目简介（中文）
├── USER_GUIDE_zh.md             # 用户手册（中文）← 本文件
├── USER_GUIDE_en.md             # 用户手册（英文）
└── LICENSE                      # MIT 许可证
```

---

> **技术支持**: https://github.com/zhouliang-sjtu/codespect-matrix/issues  
> **项目主页**: https://github.com/zhouliang-sjtu/codespect-matrix
