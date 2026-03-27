# Novel Runtime 架构规划 v1

> 基于《项目功能对比总表 v2》的选型结论，本文档聚焦工程落地：合理性审查、全量功能要素图、模块分层、CLI 命令树、Roadmap。
>
> 前置共识：
> - 最优单选基底：InkOS
> - 最优组合：InkOS + novelwriter2 + NovelForge
> - 参考增强：arboris-novel、novel-writer
> - CLI-Anything 采用"选择性借用"模式：Phase 2/4/5/6/6.5/7 直接可用，Phase 1 不适用（需跳过），Phase 3 需适配；不作为小说业务内核
> - 真正负责"定真"的只能是 canonical state
> - summary / RAG / KG 只能辅助召回，不能负责定真

---

## 一、方案是否合理：结论

**合理，但有明确边界。**

用 CLI-Anything 的思路做"全量功能要素图 + 增量 CLI 化改造"的终极小说系统，整体方向正确。但必须严格区分三件事：

1. **CLI-Anything 提供的是打包模式**（怎么把能力暴露给 agent）
2. **Novel Runtime 提供的是业务内核**（小说状态如何被维护和治理）
3. **Novel Skill 提供的是编排策略**（不同场景走什么流程）

三者缺一不可，但绝不能混为一谈。

---

## 二、为什么合理 / 不合理（任务 A）

### 2.1 用 CLI-Anything 作为外层 CLI/Skill 打包模式是否合理？

**合理。** 原因：

| 维度 | 判断 | 说明 |
|------|------|------|
| CLI 化打包 | ✅ 直接适用 | Click + REPL + `--json` + `SKILL.md` 的模式可以直接套用 |
| 命令发现性 | ✅ 直接适用 | `--help`、`which novel`、REPL banner 自带 skill path |
| agent 可调用性 | ✅ 直接适用 | JSON 输出 + 结构化错误 + 退出码，agent 原生友好 |
| 测试框架 | ✅ 可参考 | 4 层测试模型（unit / e2e-native / e2e-backend / subprocess）可沿用 |
| 状态管理 | ⚠️ 需要替换 | CLI-Anything 的 session.py 是文档级 undo/redo，小说系统需要章节级 canonical state + snapshot/rollback，复杂度高一个数量级 |
| 业务逻辑 | ❌ 不适用 | CLI-Anything 的核心是"给 GUI 软件生成 CLI 接口"，小说系统没有外部 GUI 后端可调 |

### 2.2 它能解决什么？

1. **CLI 骨架**：Click group/command 结构、REPL skin、`--json` flag
2. **打包分发**：PEP 420 namespace package、`pip install -e .`、`console_scripts` entry point
3. **Skill 发现**：`SKILL.md` 自动生成模板、banner 展示 skill path
4. **测试规范**：`TEST.md` + 4 层测试 SOP
5. **agent 接口契约**：结构化输出、错误格式、退出码约定

### 2.3 它不能解决什么？

1. **canonical state 存储与治理** —— 这是小说系统的核心难题，CLI-Anything 没有对应物
2. **上下文装配与可见性裁剪** —— 小说特有，需要从 novelwriter2 移植
3. **章节结算、审计、修订** —— 小说特有流水线，需要从 InkOS 移植
4. **快照、回滚、diff** —— 需要自建，CLI-Anything 的 undo/redo 是内存级的
5. **确定性规则引擎** —— 需要自建或从 InkOS 移植
6. **知识图谱、卡片系统** —— 需要从 NovelForge 参考

### 2.4 它和 Novel Runtime 的边界在哪里？

```
┌──────────────────────────────────────────────────────────┐
│                    Novel Skill (SKILL.md)                 │
│  流程编排 / 场景判断 / 命令组合策略 / agent 使用说明        │
├──────────────────────────────────────────────────────────┤
│                    Novel CLI (Click)                      │
│  稳定命令面 / JSON 输出 / REPL / 可测试 / 可脚本化         │
│  ← CLI-Anything 模式直接适用的范围                         │
├──────────────────────────────────────────────────────────┤
│                    Novel Runtime                          │
│  canonical state / context assembly / settle / audit      │
│  postcheck / snapshot / rollback / rules engine           │
│  ← CLI-Anything 完全不涉及的范围，需要自建                 │
└──────────────────────────────────────────────────────────┘
```

**一句话：CLI-Anything 管"怎么暴露能力"，Novel Runtime 管"能力本身"。**

### 2.5 这种路线相比"直接做插件"或"直接做前端应用"，为什么更合理？

| 路线 | 优势 | 劣势 | 适合阶段 |
|------|------|------|----------|
| **Runtime + CLI + Skill** | 内核可独立测试、可被任意 agent/UI 调用、关注点分离 | 初期无可视化界面 | **当前最优** |
| 直接做 Claude Skill/Plugin | 启动快、agent 直接可用 | 能力全靠 prompt 驱动，无状态治理，一致性无法保证 | 不适合当前目标 |
| 直接做前端应用 | 用户体验好 | 会把精力分散到 UI，核心一致性机制容易被绕过或弱化 | 后期再做 |
| 直接做 MCP server | 可被多种客户端调用 | MCP 只是传输协议，不解决业务内核问题 | 可作为外层接口，不能作为起点 |

---

## 三、全量功能要素图（任务 B）

### 3.1 Runtime 层功能

| 功能模块 | 子功能 | 来源项目 | 必须保留 | 优先级 | 对一致性价值 | 迁移方式 |
|----------|--------|----------|----------|--------|-------------|----------|
| **Canonical State Store** | 唯一事实源存储（角色、地点、物品、关系、时间线、伏笔） | InkOS(truth files) + novelwriter2(world model) | ✅ | P0 | 最高——系统根基 | 改造后移植：合并 truth files 与 world model 设计 |
| **World Model Schema** | 实体-属性-关系的结构化 schema 定义 | novelwriter2(world entities) + NovelForge(card/schema) | ✅ | P0 | 最高——定义"什么是事实" | 改造后移植：取 novelwriter2 实体模型 + NovelForge schema 校验 |
| **Context Assembly** | 按角色/场景/可见性装配 writer/checker/planner 上下文 | novelwriter2(context_assembly.py, Aho-Corasick) | ✅ | P0 | 最高——直接控制幻觉 | 直接移植 |
| **Visibility Gating** | active/reference/hidden 三级可见性，Writer 不可见 hidden | novelwriter2(world_visibility.py) | ✅ | P0 | 最高——防剧透/防信息泄露 | 直接移植 |
| **Chapter Settler** | 章节写完后自动结算：更新角色状态、推进伏笔、更新关系 | InkOS(两阶段写作, settler) | ✅ | P0 | 最高——保证下章上下文正确 | 直接移植核心逻辑 |
| **Deterministic Postcheck Gate** | 零 LLM 硬规则：新名词/新称号/时间线跳变/未授权出场/AI 套话 | novelwriter2(continuation_postcheck.py) + arboris-novel(chapter_guardrails.py) + novel-writer(text-audit.sh) | ✅ | P0 | 最高——拦硬错误 | 改造后移植：合并三个来源的规则 |
| **Snapshot / Rollback** | 每章快照、状态 diff、修订 diff、任意章节回滚 | InkOS(snapshot) | ✅ | P0 | 最高——长篇必备 | 直接移植 |
| **Rules Engine (3-layer)** | 通用规则 + 题材规则 + 单书规则 | InkOS(rules) + novel-writer(validation-rules.json) | ✅ | P0 | 高——规则可扩展 | 改造后移植 |
| **Audit System** | 多维度审计（LLM + 纯规则混合），分级：blocker/major/minor | InkOS(33维度 ContinuityAuditor) | ✅ | P1 | 高——发现深层问题 | 改造后移植 |
| **Reviser** | spot-fix 模式修订 + AI 标记守卫（修订后 AI 味增多则丢弃） | InkOS(ReviserAgent + AI guard) | ✅ | P1 | 高——安全修订 | 直接移植 |
| **Temperature Separation** | 创作(T=0.7) / 结算(T=0.3) / 再审(T=0) | InkOS | ✅ | P1 | 高——降低随机性 | 仅参考思路（配置化） |
| **Style Anchor / Fingerprint** | 统计文风指纹 + 风格指南注入 | InkOS(style clone) + novelwriter2(style anchor) | ✅ | P1 | 中高——防文风漂移 | 改造后移植 |
| **Import / Bootstrap** | 导入既有小说 → 自动建立 world model + canonical state | InkOS(import/canon/spinoff) + novelwriter2(bootstrap) | ✅ | P1 | 高——续写必备 | 改造后移植 |
| **Foreshadow Tracker** | 长线伏笔注册、推进、到期提醒、回收 | InkOS(pending_hooks) + arboris-novel | ✅ | P1 | 高——长篇核心 | 改造后移植 |

### 3.2 CLI 层功能

| 功能模块 | 子功能 | 来源项目 | 必须保留 | 优先级 | 迁移方式 |
|----------|--------|----------|----------|--------|----------|
| **Project Management** | init / open / info / config | CLI-Anything(通用模式) | ✅ | P0 | 参考模式新建 |
| **World / Character / Setting** | create / update / list / show / delete 实体 | novelwriter2 + NovelForge | ✅ | P0 | 参考思路新建 |
| **Outline Management** | generate / show / update / approve 大纲 | arboris-novel + InkOS | ✅ | P1 | 参考思路新建 |
| **Chapter Lifecycle** | draft / settle / audit / revise / approve / export | InkOS | ✅ | P0 | 直接映射 Runtime |
| **State Inspection** | show / diff / timeline / relationships / hooks | InkOS + novelwriter2 | ✅ | P0 | 直接映射 Runtime |
| **Snapshot / Rollback** | create / list / diff / rollback / delete | InkOS | ✅ | P0 | 直接映射 Runtime |
| **Import / Export** | import-book / export-epub / export-markdown | InkOS + novelwriter2 | ✅ | P1 | 直接映射 Runtime |
| **Inspect / Debug** | rules / audit-report / postcheck-report / style-report | InkOS | ⚠️ | P2 | 参考思路新建 |
| **REPL Mode** | 交互式命令行 + 命令历史 + tab 补全 | CLI-Anything(repl_skin.py) | ✅ | P1 | 直接移植模式 |
| **JSON Output** | 所有命令 `--json` flag | CLI-Anything | ✅ | P0 | 直接移植模式 |

### 3.3 Skill 层功能

> **修正认知：** 这里的 Skill 指的是“流程外壳 / 编排层”，不是把来源项目的硬编码能力整体搬进 Skill。大多数来源项目是 pre-skill 时代的硬编码系统，真正可进入 Skill 的通常只是其可解耦的工作流顺序、提问模板和多命令编排外壳。

| 功能模块 | 说明 | 来源参考 | 优先级 | 进入 Skill 的前提 |
|----------|------|----------|--------|------------------|
| **新书启动流程** | init → world setup → characters → outline → approve | InkOS + NovelForge | P1 | CLI 已具备 project/world/outline 原子命令 |
| **章节续写流程** | context assembly → draft → settle → postcheck → audit → revise → snapshot | InkOS | P0 | Runtime 已返回 `recommended_action` / `severity`，Skill 只读 JSON 编排 |
| **一致性修复流程** | state diff → identify drift → spot-fix → re-audit | InkOS | P1 | Runtime 已返回 `drift_items` / `fix_suggestions` |
| **导入旧书流程** | import → bootstrap state → postcheck → manual review | InkOS + novelwriter2 | P1 | CLI 已具备 import/bootstrap/verify 原子命令 |
| **风格迁移流程** | analyze style → generate fingerprint → anchor → validate | InkOS + novelwriter2 | P2 | style fingerprint / anchor 已落在 Runtime/CLI |
| **伏笔巡检流程** | list hooks → check expiry → suggest resolution | InkOS + arboris-novel | P2 | Runtime 已返回 `expired` / `at_risk` |
| **审查重写流程** | full audit → triage → batch revise → re-audit → approve | InkOS + arboris-novel | P2 | Runtime 已输出 blocker/major/minor + `recommended_action` |
| **终章收束流程** | check all hooks → verify arcs → final audit → export | 自建 | P3 | 弧线完整性验证已在 Runtime 程序化 |
| **批量质量审计** | text-audit + consistency-check + AI-taste audit | novel-writer | P2 | `novel inspect text-audit` 等 CLI 原子命令已存在 |

### 3.4 prompts-assets 层功能

> **这一层是非代码资产层。** 凡是可替换的 prompt 模板、题材模板、问卷、rubric、示例、风格指南、审计文案、workflow 说明，都不应误归到 Skill 或 CLI。它们由 Runtime/CLI/Skill 消费，但自身不负责状态更新、结构化路由或确定性判断。

| 功能模块 | 说明 | 来源参考 | 优先级 |
|----------|------|----------|--------|
| **Prompt Templates** | draft / revise / audit / summarize / detect / style 等提示词模板 | AI_NovelGenerator + AI_Gen_Novel + NovelForge | P1 |
| **Audit Rubrics / Checklist** | 质量清单、审查 rubric、反 AI 味规则文本、番外审查说明 | chinese-novelist-skill + novel-writer + InkOS | P1 |
| **Genre / Style Templates** | 题材模板、风格锚定模板、世界观模板、角色模板 | chinese-novelist-skill + AI_NovelGenerator | P1 |
| **Workflow Questionnaires** | 五问启动、雪花创作法每步问题、市场调研问题集 | chinese-novelist-skill + NovelForge + InkOS | P2 |
| **Example I/O Assets** | 审计报告样例、章节输入输出样例、world bootstrap 样例 | InkOS + novelwriter2 + NovelForge | P2 |
| **Prompt DSL / Reference Snippets** | `@角色卡[...]`、上下文注入片段、规则说明文本 | NovelForge + InkOS | P2 |

### 3.5 可选未来外层

| 外层类型 | 说明 | 优先级 |
|----------|------|--------|
| MCP Server | 把 Novel CLI 能力通过 MCP 协议暴露给任意 MCP client | P2 |
| Claude Code Plugin | 把 Novel Skill 做成 Claude Code 插件 | P2 |
| Web API / REST | 给前端或第三方系统调用 | P3 |
| Desktop GUI | Electron/Tauri 前端 | P3 |
| VS Code Extension | 编辑器内集成 | P3 |

---

## 四、技术选型与模块分层

### 4.1 技术栈选择

| 层级 | 推荐技术栈 | 理由 |
|------|-----------|------|
| Runtime | **Python 3.12+** | InkOS/novelwriter2/NovelForge 核心逻辑均为 Python/TypeScript，Python 生态更适合 CLI + NLP + 数据处理；novelwriter2 核心模块（context_assembly、postcheck）已是 Python |
| CLI | **Click 8.x** + **prompt-toolkit** | CLI-Anything 验证过的成熟方案 |
| 存储 | **JSON/YAML 文件** (MVP) → **SQLite** (增强期) | 文件存储简单可 diff 可 git 追踪，SQLite 后期加关系查询 |
| Skill | **Markdown (SKILL.md)** | CLI-Anything 标准模式 |
| 测试 | **pytest** | 标准 Python 测试框架 |
| 打包 | **PEP 420 namespace package** | CLI-Anything 标准模式 |

### 4.2 目录结构

```
novel/
├── novel-runtime/                     # Runtime 核心包
│   ├── novel_runtime/
│   │   ├── __init__.py
│   │   ├── state/                     # Canonical State
│   │   │   ├── canonical.py           # 唯一事实源
│   │   │   ├── world_model.py         # 实体-属性-关系
│   │   │   ├── schema.py              # Schema 定义与校验
│   │   │   ├── snapshot.py            # 快照 / 回滚 / diff
│   │   │   └── migration.py           # 状态迁移
│   │   ├── context/                   # 上下文装配
│   │   │   ├── assembly.py            # Writer/Checker/Planner 上下文装配
│   │   │   ├── visibility.py          # 可见性裁剪
│   │   │   └── token_budget.py        # Token budget 管理
│   │   ├── pipeline/                  # 写作流水线
│   │   │   ├── drafter.py             # 章节草稿生成（含 scene-level iteration）
│   │   │   ├── settler.py             # 章节结算
│   │   │   ├── auditor.py             # 多维审计
│   │   │   ├── reviser.py             # 修订 + AI 守卫
│   │   │   ├── postcheck.py           # 确定性 postcheck gate
│   │   │   └── router.py             # Confidence routing（audit→pass/revise/rewrite/escalate）
│   │   ├── rules/                     # 规则引擎
│   │   │   ├── engine.py              # 三层规则引擎
│   │   │   ├── universal.py           # 通用规则
│   │   │   ├── genre/                 # 题材规则目录
│   │   │   └── book_rules.py          # 单书规则
│   │   ├── knowledge/                 # 知识层（P1）
│   │   │   ├── foreshadow.py          # 伏笔追踪
│   │   │   ├── style.py               # 风格锚定/指纹
│   │   │   └── kg.py                  # 知识图谱（P2）
│   │   ├── import_export/             # 导入导出
│   │   │   ├── importer.py            # 导入既有作品
│   │   │   ├── bootstrapper.py        # 自动建立 world model
│   │   │   └── exporter.py            # 导出 EPUB/Markdown/etc
│   │   ├── orchestration/             # 可选编排层（P2）
│   │   │   ├── chief.py              # Chief 决策层
│   │   │   ├── deputy.py             # Deputy 调度层
│   │   │   ├── shared_context.py     # 跨 agent 上下文共享
│   │   │   └── confidence.py         # 置信度路由
│   │   └── llm/                       # LLM 调用抽象层
│   │       ├── provider.py            # 模型提供者抽象
│   │       ├── temperature.py         # 温度策略
│   │       ├── resilience.py          # 错误分类/退避/队列/限速/状态追踪
│   │       └── agent_session.py       # 工具调用式对话会话（React/Tool Agent）
│   ├── tests/
│   └── setup.py
│
├── novel-cli/                         # CLI 包（依赖 novel-runtime）
│   ├── cli_anything/                  # PEP 420 namespace（无 __init__.py）
│   │   └── novel/
│   │       ├── __init__.py
│   │       ├── novel_cli.py           # Click 主入口
│   │       ├── commands/              # 命令分组
│   │       │   ├── project.py
│   │       │   ├── world.py
│   │       │   ├── outline.py
│   │       │   ├── chapter.py
│   │       │   ├── state.py
│   │       │   ├── snapshot.py
│   │       │   ├── import_cmd.py
│   │       │   ├── inspect.py
│   │       │   ├── detect.py
│   │       │   ├── style.py
│   │       │   ├── genre.py
│   │       │   ├── analytics.py
│   │       │   ├── prompt.py
│   │       │   ├── rules.py
│   │       │   ├── daemon.py
│   │       │   ├── agent.py           # agent chat/run/status
│   │       │   ├── doctor.py
│   │       │   ├── stats.py
│   │       │   └── radar.py
│   │       ├── utils/
│   │       │   └── repl_skin.py       # 从 CLI-Anything 移植
│   │       ├── skills/
│   │       │   └── SKILL.md
│   │       └── tests/
│   │           ├── TEST.md
│   │           ├── test_core.py
│   │           └── test_e2e.py
│   └── setup.py
│
└── docs/                              # 文档
    ├── architecture-novel-runtime-v1.md  # 本文档
    └── ...
```

---

## 五、Novel CLI 命令树草案

```
novel
├── project
│   ├── init          # 初始化新项目
│   ├── open          # 打开已有项目
│   ├── info          # 显示项目信息
│   ├── config        # 项目配置（模型、温度、规则集等）
│   └── export        # 导出项目（EPUB / Markdown / JSON）
│
├── world
│   ├── create        # 创建世界设定
│   ├── show          # 显示世界状态
│   ├── update        # 更新世界设定
│   ├── entity
│   │   ├── add       # 添加实体（角色/地点/物品/势力）
│   │   ├── update    # 更新实体属性
│   │   ├── show      # 显示实体详情
│   │   ├── list      # 列出所有实体
│   │   └── delete    # 删除实体
│   └── relationship
│       ├── add       # 添加关系
│       ├── update    # 更新关系
│       ├── list      # 列出关系
│       └── graph     # 显示关系图（文本格式）
│
├── outline
│   ├── generate      # 生成大纲
│   ├── show          # 显示大纲
│   ├── update        # 更新大纲节点
│   └── approve       # 确认大纲
│
├── chapter
│   ├── draft         # 生成章节草稿（创作阶段，T=0.7）
│   ├── settle        # 结算章节状态（结算阶段，T=0.3）
│   ├── postcheck     # 运行确定性检查 gate
│   ├── audit         # 运行多维审计
│   ├── revise        # 执行修订（spot-fix 模式）
│   ├── approve       # 人工放行
│   ├── show          # 显示章节内容 + 元信息
│   ├── list          # 列出所有章节
│   └── rewrite       # 全章重写（blocker 级别时使用）
│
├── state
│   ├── show          # 显示当前 canonical state 摘要
│   ├── diff          # 两个版本之间的状态差异
│   ├── timeline      # 显示时间线
│   ├── hooks         # 显示未回收伏笔
│   ├── characters    # 显示角色当前状态一览
│   └── validate      # 验证状态一致性
│
├── snapshot
│   ├── create        # 创建快照
│   ├── list          # 列出所有快照
│   ├── diff          # 比较两个快照
│   ├── rollback      # 回滚到指定快照
│   └── delete        # 删除快照
│
├── import
│   ├── book          # 导入既有小说文本
│   ├── bootstrap     # 从导入文本自动建立 world model
│   └── verify        # 验证导入后状态
│
├── inspect
│   ├── rules         # 显示当前生效规则
│   ├── audit-report  # 显示最近审计报告
│   ├── postcheck-report # 显示最近 postcheck 报告
│   ├── style-report  # 显示风格分析报告
│   └── text-audit    # 运行离线文本审计（连接词/AI 味/句长等）
│
├── rules
│   ├── list          # 列出规则
│   ├── add           # 添加规则
│   ├── update        # 更新规则
│   ├── disable       # 禁用规则
│   └── test          # 对文本测试规则
│
└── session
    ├── status        # 当前会话状态
    └── history       # 命令历史
```

---

## 六、哪些能力进 Runtime，哪些进 CLI，哪些进 Skill

### 6.1 必须下沉到 Runtime（绝不能只靠 Skill/prompt）

| 能力 | 原因 |
|------|------|
| Canonical State 读写与治理 | 这是唯一事实源，prompt 不可能稳定维护 |
| World Model schema 定义与校验 | 结构化数据需要程序级保证 |
| Context Assembly + Visibility Gating | 必须是确定性裁剪，不能靠模型"自觉" |
| Chapter Settle（状态结算） | 必须程序级更新 canonical state，不能只靠 LLM 总结 |
| Deterministic Postcheck Gate | 零 LLM 硬规则，必须阻塞式 |
| Snapshot / Rollback / Diff | 文件系统级操作，必须可靠 |
| Rules Engine（三层） | 规则加载、匹配、执行必须确定性 |
| Temperature Strategy | 不同阶段的温度隔离必须程序控制 |
| AI Guard（修订安全） | 对比 AI 味指标、丢弃决策必须程序化 |
| Confidence Router | audit 结果→ pass/revise/rewrite/escalate 的路由决策必须确定性，不能靠 Skill prompt 判断 |
| LLM Resilience | 错误分类、退避策略、优先队列、动态限速必须程序化，不能靠调用方自行处理 |
| Scene-level Iteration | plan→write→embellish→memory-update 循环是生成质量的核心机制，必须在 drafter 内部实现 |
| Schema Composer | $ref 解析、$defs 注入、字段保护是 schema 校验的核心，不能只靠外部工具 |
| Foreshadow Expiry Check | 伏笔到期判断必须程序化（章节号比较），不能靠 LLM 判断 |
| Drift Detection | 状态漂移检测（新名词/关系变化/时间线跳变）必须确定性，不能只靠 Skill 编排 |

### 6.0 严格分层判定表（Runtime / CLI / Skill / prompts-assets）

| 能力/模块 | 建议归属层 | 为什么必须归这层 | 前提条件 | 典型产物 |
|----------|-----------|------------------|----------|----------|
| Canonical State / World Model / Schema / Drift Detection / Snapshot | **Runtime** | 涉及状态治理、结构化校验、确定性更新、回滚与 diff，不能靠 prompt 或 Skill 稳定维护 | 无，属于底座 | `novel_runtime/state/*` |
| Context Assembly / Visibility / Settler / Postcheck / Audit / Router / Reviser / Resilience | **Runtime** | 涉及规则执行、严重级别分级、推荐动作路由、错误恢复与温度策略，属于功能本体 | 无或依赖底层 schema/state 已存在 | `novel_runtime/context/*`, `pipeline/*`, `llm/*` |
| project/world/chapter/state/snapshot/import/inspect/rules/agent 等稳定原子操作 | **CLI** | 本质是对 Runtime 能力的离散暴露，要求可调用、可测试、可脚本化、可 `--json` | 对应 Runtime 能力已存在 | `novel-cli/cli_anything/novel/commands/*` |
| 新书启动 / 导入旧书 / 多版本择优 / 雪花创作法 / 五问启动 / 批量质量审计 等多步流程 | **Skill** | 它们是多个 CLI 原子命令的组合，价值在流程顺序、人工确认点和编排，而不是底层执行保障 | 依赖所需 CLI 原子命令已存在；若含判断分支，还需 Runtime JSON 字段 | `skills/<workflow>/SKILL.md` 或 `novel-dev-sop` references |
| 章节续写 / 一致性修复 / 伏笔巡检 / 审查重写 / 终章收束 等含条件分支流程 | **Skill（受限）** | 只能做流程外壳；其中 revise/rewrite、drift、expiry、severity 等判断绝不能写在 Skill | Runtime 必须返回 `recommended_action` / `severity` / `drift_items` / `fix_suggestions` / `expired` / `at_risk` 等 JSON 字段 | `skills/<workflow>/SKILL.md` + CLI JSON 契约 |
| Prompt 模板 / 审计 rubric / 题材模板 / 风格模板 / 五问问卷 / 示例输入输出 | **prompts-assets** | 它们是可替换的内容资产，不负责状态更新、结构化路由或规则执行；如果不单列，会被误塞进 Skill 或 CLI | 被 Runtime/CLI/Skill 消费即可 | `prompts/`, `templates/`, `rules/`, `references/`, `assets/` |

### 6.1 必须下沉到 Runtime（绝不能只靠 Skill/prompt）

| 命令 | 原因 |
|------|------|
| `chapter draft/settle/postcheck/audit/revise/approve` | 章节生命周期的每一步都是明确的原子操作 |
| `state show/diff/timeline/hooks/characters/validate` | 状态查询是高频基础操作 |
| `snapshot create/list/diff/rollback` | 快照操作是明确的 CRUD |
| `world entity add/update/show/list` | 实体管理是明确的 CRUD |
| `import book/bootstrap/verify` | 导入流程的每一步是明确的 |
| `inspect rules/audit-report/postcheck-report` | 审查报告查询是只读操作 |
| `project init/open/info/config/export` | 项目管理是标准 CLI 模式 |

### 6.3 适合放在 Skill 里做灵活编排

> **核心原则：Skill 只做纯编排（调用顺序 + 条件分支读取），所有判断逻辑的硬编码必须在 Runtime 实现，Skill 只读取 CLI 返回的 JSON 中的 `recommended_action` / `severity` / `expired` 等字段来决定下一步。**
>
> **补充澄清：** 不能因为来源项目“看起来像工作流”就把它直接归到 Skill。对于 pre-skill 时代项目，绝大多数流程其实是“代码内嵌流程”：规则、状态更新、分级、路由、校验都写在程序里。真正进入 Skill 的，只能是这些硬逻辑之上的可解耦外壳：步骤顺序、提问流程、人工决策点、以及多个 CLI 原子命令的组合。

| 流程 | 原因 | 依赖的 Runtime 硬逻辑 |
|------|------|----------------------|
| 新书启动（init → world → outline → approve） | 步骤顺序可能因场景变化 | 无，纯编排 |
| 章节续写（assembly → draft → settle → ... → snapshot） | 是多个 CLI 命令的组合，有条件分支 | `router.py` 返回 `recommended_action`，Skill 据此分支 |
| 一致性修复（state diff → identify → fix → re-audit） | 诊断+修复流程因情况而异 | `state validate` 返回 `drift_items` + `fix_suggestions`，Skill 据此编排 |
| 导入旧书（import → bootstrap → postcheck → review） | 步骤固定但人工介入点灵活 | 无，纯编排 |
| 伏笔巡检 | 触发条件和处理策略因书而异 | `foreshadow.py` 返回 `expired` + `at_risk`，Skill 据此编排 |
| 终章收束 | 检查维度和收束策略因题材而异 | `auditor.py` 返回弧线完整性检查结果，Skill 据此编排 |
| 批量质量审计 | 审计范围和阈值因需求而异 | 无，纯编排（循环调用 text-audit） |
| 多版本择优 | draft N versions → compare → select | 无，纯编排 |
| 雪花创作法 | NovelForge 工作流步骤顺序 | 无，纯编排 |
| 番外写作 | import canon → setup → draft → spinoff audit | `auditor.py` 的 4 个番外专用维度在 Runtime 实现 |
| 五问启动 | 5 问采集 → 大纲确认 → 开始创作 | 无，纯编排 |
| 风格迁移 | analyze → fingerprint → anchor → validate | 无，纯编排 |
| 审查重写 | full audit → triage → batch revise → re-audit | `auditor.py` 返回 `severity` 分级，`router.py` 返回 `recommended_action` |
| 市场调研 | radar → analyze → genre select → outline adjust | 无，纯编排 |
| 写作统计 | 追踪字数/进度/成本 → 生成报告 | 无，纯编排 |

### 6.4 来源项目 → 四层归属映射表（基于代码证据）

> **方法论**：以下分类基于实际目录结构和源代码阅读，不是推测。判断标准：
> - 凡含状态管理/规则判断/pipeline/LLM抽象/数据校验的硬编码 → **Runtime**
> - 凡可独立调用的原子命令 → **CLI**
> - 凡多命令编排且本身不含判断逻辑的流程外壳 → **Skill**
> - 凡可替换的 prompt 模板/题材模板/问卷/rubric/文案 → **prompts-assets**

#### InkOS（TypeScript monorepo，最成熟的来源项目）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 状态管理器 | `packages/core/src/state/manager.ts` |
| **Runtime** | 5-Agent 流水线（architect/continuity/post-write-validator/radar/detector） | `packages/core/src/agents/*.ts` |
| **Runtime** | Pipeline runner/scheduler/detection-runner | `packages/core/src/pipeline/*.ts` |
| **Runtime** | LLM 抽象层 | `packages/core/src/llm/` |
| **Runtime** | 通知分发 | `packages/core/src/notify/` |
| **CLI** | 20 个原子命令（agent/analytics/audit/book/config/daemon/detect/doctor/draft/export/genre/import/init/radar/review/revise/status/style/update/write） | `packages/cli/src/commands/*.ts` |
| **Skill** | Agent 模式（LLM 驱动的 tool-use 调度外壳）+ `skills/SKILL.md` 描述的 5-agent 编排 | `packages/core/src/pipeline/agent.ts`, `skills/SKILL.md` |
| **prompts-assets** | 题材专属规则（恐怖/仙侠/都市/玄幻/其他）、通用创作规则、写手/settler prompt 模板 | `.qoder/repowiki/zh/content/题材与规则系统/`, `packages/core/src/agents/writer-prompts.ts`, `packages/core/genres/*.md` |

#### NovelForge（Python + Vue 全栈 Web 应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | Schema 合成/\$ref 解析/字段保护 | `backend/app/services/schema_service.py` |
| **Runtime** | 知识图谱/关系提取 | `backend/app/services/knowledge_service.py`, `kg_provider.py`, `relation_graph_service.py` |
| **Runtime** | Workflow 引擎（节点/触发器/注册/解析/执行） | `backend/app/services/workflow/engine/`, `registry.py`, `triggers.py` |
| **Runtime** | AI 生成/Tool Agent/流式 SSE | `backend/app/services/ai/core/`, `generation/`, `workflow_agent/` |
| **Runtime** | 卡片系统 CRUD + 导出 | `backend/app/services/card_service.py`, `card_export_service.py` |
| **Runtime** | 伏笔服务/上下文服务/记忆服务 | `backend/app/services/foreshadow_service.py`, `context_service.py`, `memory_service.py` |
| **CLI** | 无独立 CLI；通过 REST API 暴露 | `backend/app/api/endpoints/` |
| **Skill** | Workflow Agent（自然语言编写/修改工作流）+ 雪花创作法编排 | `backend/app/services/ai/workflow_agent/agent_service.py` |
| **prompts-assets** | @DSL 上下文注入模板、提示词工坊 prompt、bootstrap 内置提示词集 | `backend/app/services/prompt_service.py`, `backend/app/bootstrap/prompts/*.txt` |

#### novelwriter2（Python FastAPI Web 应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 上下文组装（Aho-Corasick） | `app/core/context_assembly.py` |
| **Runtime** | 续写后验（postcheck） | `app/core/continuation_postcheck.py` |
| **Runtime** | World Model CRUD / bootstrap / worldpack 导入 | `app/core/world_crud.py`, `world_application.py`, `worldpack_import.py`, `bootstrap.py` |
| **Runtime** | Lore manager / visibility / window index | `app/core/lore_manager.py`, `app/world_visibility.py`, `app/core/window_index.py` |
| **Runtime** | Generator / AI client / rate limiting / safety fuses | `app/core/generator.py`, `ai_client.py`, `rate_limit.py`, `safety_fuses.py` |
| **CLI** | 管理脚本（去重/章节同步）；无面向用户的独立 CLI | `scripts/novel_admin.py`, `app/api/` |
| **Skill** | Worldpack 导入多步流程（plan → apply → warnings + 人工审核） | `app/core/worldpack_import.py`, `app/api/world.py` |
| **prompts-assets** | Prompt 模板注册（locale × PromptKey）、续写/系统模板 | `app/core/text/catalog.py`, `app/utils/prompts.py` |

#### newtype-profile（TypeScript Claude Code Profile/Plugin）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | Chief/Deputy/Specialist 编排框架 | `src/hooks/chief-orchestrator/` |
| **Runtime** | Confidence router（audit→pass/revise/rewrite/escalate） | `src/hooks/chief-orchestrator/confidence-router.ts` |
| **Runtime** | Background agent manager | `src/features/background-agent/` |
| **Runtime** | Session state / plugin state | `src/features/claude-code-session-state/`, `src/plugin-state.ts` |
| **Runtime** | Skill loader / merger | `src/features/opencode-skill-loader/merger.ts` |
| **CLI** | CLI 入口 | `src/cli/index.ts` |
| **Skill** | 无独立 Skill（是 Claude Code profile 系统） | — |
| **prompts-assets** | Agent 描述文档、hook 配置 | `src/features/AGENTS.md`, `src/hooks/AGENTS.md` |

#### chinese-novelist-skill（Claude Code Skill，唯一的 skill-native 项目）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 无 | — |
| **CLI** | 字数检查脚本 | `scripts/check_chapter_wordcount.py` |
| **Skill** | 三阶段章节创作流程、五问启动流程 | `SKILL.md` |
| **prompts-assets** | 11 个 reference 文档（chapter-guide/template, character-building/template, consistency, content-expansion, dialogue-writing, hook-techniques, outline-template, plot-structures, quality-checklist） | `references/*.md` |

#### novel-writer（Bash 脚本 + Prompt 模板框架）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 无（纯脚本 + Node.js CLI，无硬编码系统逻辑） | — |
| **CLI** | Node.js CLI（`novel init/check/upgrade/plugins`）+ 22 个 bash 脚本命令（text-audit, check-consistency, write-chapter, etc.） | `src/cli.ts`, `.specify/scripts/bash/*.sh` |
| **Skill** | 创作流程外壳（多脚本编排） | `docs/workflow.md` |
| **prompts-assets** | 知识模板（audit-config.json, character-profiles, character-voices, locations, world-setting）、命令模板 | `.specify/templates/knowledge/`, `.specify/templates/commands/` |

#### AI_NovelGenerator（Python 桌面应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 一致性检查器 | `consistency_checker.py` |
| **Runtime** | LLM 适配器 + Embedding 适配器 | `llm_adapters.py`, `embedding_adapters.py` |
| **Runtime** | 章节生成 pipeline + Vector RAG | `main.py`, `novel_generator/chapter.py`, `novel_generator/vectorstore_utils.py` |
| **CLI** | 无独立 CLI（GUI） | — |
| **Skill** | 无 | — |
| **prompts-assets** | **所有 prompt 集中定义**（摘要/关键词/章节写作/审计/雪花法步骤等） | `prompt_definitions.py` |

#### AI_Gen_Novel（Python RecurrentGPT 实现）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | RecurrentGPT 循环（plan→write→embellish→memory） | `AIGN.py` |
| **Runtime** | LLM 统一接口 | `LLM.py`, `uniai/` |
| **CLI** | 无独立 CLI（Gradio UI） | — |
| **Skill** | 无 | — |
| **prompts-assets** | **所有 prompt 集中定义**（大纲/开头/续写/润色/记忆 prompt） | `AIGN_Prompt.py` |

#### arboris-novel（Python FastAPI + Vue Web 应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | Pipeline orchestrator / guardrails / pacing / self-critique / reader simulation | `backend/app/core/`, `backend/app/services/`, `backend/app/tasks/` |
| **Runtime** | DB 层 + 存储 | `backend/db/`, `backend/storage/` |
| **CLI** | 无独立 CLI；通过 REST API | `backend/app/api/` |
| **Skill** | 无 | — |
| **prompts-assets** | **10+ prompt 模板**（chapter_plan, character_dna_guide, concept, constitution_check, editor_review, evaluation, extraction, faction_context, foreshadowing_reminder, import_analysis） | `backend/prompts/*.md` |

#### Long-Novel-GPT（Python Gradio/Streamlit 应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 多层级写作器（outline→plot→draft→summary）、diff 工具 | `core/outline_writer.py`, `plot_writer.py`, `draft_writer.py`, `summary_novel.py`, `diff_utils.py` |
| **Runtime** | LLM API 抽象 | `llm_api/` |
| **CLI** | 无独立 CLI（Web UI） | — |
| **Skill** | 无 | — |
| **prompts-assets** | **分门别类的 prompt 模板**（创作剧情/创作章节/创作正文，每类含新建/扩写/润色/格式化） | `prompts/创作剧情/`, `prompts/创作章节/`, `prompts/创作正文/` |

#### NovelGenerator（TypeScript React 前端应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | Gemini 服务调用 | `services/geminiService.ts` |
| **CLI** | 无 | — |
| **Skill** | 无 | — |
| **prompts-assets** | 内嵌 prompt | `constants.ts` |

#### NovelWriter3（Python 多 agent 桌面应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 多级审查 / genre 生成器 / 质量趋势 | `core/generation/`, `agents/` |
| **CLI** | CLI 入口 | `main.py` |
| **Skill** | 无 | — |
| **prompts-assets** | 内嵌 prompt | — |

#### AI-automatically-generates-novels（Python 多模型 Web 应用）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 多模型适配（ChatGPT/Claude/DeepSeek/Gemini/Ollama/通义千问/文心/豆包） | `apps/app-*.py` |
| **Runtime** | AI 打分 + 迭代重写 + 去AI味 | `app.py` |
| **CLI** | 无（Web UI） | — |
| **Skill** | 无 | — |
| **prompts-assets** | 提示词优化文档 | `提示词优化.md` |

#### novelWriter（Python Qt 桌面编辑器）

| 归属层 | 能力 | 证据路径 |
|--------|------|----------|
| **Runtime** | 编辑器核心 / 格式导出 / 扩展 / 项目树 / 索引 / 备份 | `novelwriter/core/`, `formats/`, `extensions/` |
| **CLI** | 无（纯 GUI） | — |
| **Skill** | 无 | — |
| **prompts-assets** | 无（纯编辑器，无 AI prompt） | — |

#### 汇总统计

| 来源项目 | Runtime | CLI | Skill | prompts-assets | 原始形态 |
|----------|---------|-----|-------|----------------|----------|
| **InkOS** | ★★★★★ | ★★★★★ | ★★ | ★★★ | TypeScript monorepo CLI |
| **NovelForge** | ★★★★★ | — | ★★ | ★★★ | Python+Vue Web 全栈 |
| **novelwriter2** | ★★★★ | ★ | ★ | ★★ | Python FastAPI Web |
| **newtype-profile** | ★★★★ | ★ | — | ★ | TS Claude Code Profile |
| **arboris-novel** | ★★★ | — | — | ★★★ | Python FastAPI Web |
| **Long-Novel-GPT** | ★★★ | — | — | ★★★ | Python Gradio Web |
| **AI_NovelGenerator** | ★★★ | — | — | ★★★ | Python 桌面 GUI |
| **AI_Gen_Novel** | ★★ | — | — | ★★★ | Python Gradio |
| **chinese-novelist-skill** | — | ★ | ★★★★ | ★★★★★ | Claude Code Skill |
| **novel-writer** | — | ★★★ | ★★ | ★★★★ | Bash 脚本框架 |
| **NovelWriter3** | ★★ | ★ | — | ★ | Python CLI |
| **NovelGenerator** | ★ | — | — | ★ | TS React 前端 |
| **AI-auto-generates-novels** | ★★ | — | — | ★ | Python Web |
| **novelWriter** | ★★★ | — | — | — | Python Qt 编辑器 |

> **关键发现**：14 个来源项目中，**仅 chinese-novelist-skill 是 skill-native**；其余 13 个全部是 pre-skill 硬编码系统。Runtime 贡献最大的是 InkOS（唯一既有 Runtime 又有完整 CLI 的项目）和 NovelForge（最丰富的 Runtime 能力集）。prompts-assets 贡献最大的是 chinese-novelist-skill（11 个 reference）、AI_NovelGenerator（集中式 prompt_definitions.py）、arboris-novel（10+ prompt 模板）和 Long-Novel-GPT（分类 prompt 目录）。InkOS 和 NovelForge 各自有一种 agent 模式作为 Skill 层贡献（InkOS 的 tool-use agent loop，NovelForge 的 Workflow Agent），但这些 Skill 层能力嵌入在项目代码中，需解耦后才能移植。

---

## 七、Roadmap（分阶段）

### Phase 0：架构冻结 / 边界明确

**阶段目标：** 确定技术选型、模块边界、数据模型，产出可执行的设计文档。

**交付物：**
- [x] 本文档（architecture-novel-runtime-v1.md）
- [ ] Canonical State schema 设计文档（JSON Schema 草案）
- [ ] World Model entity/relationship schema 设计
- [ ] Rules Engine 规则格式定义
- [ ] LLM 调用抽象层接口定义

**涉及模块：** 全部（设计层面）

**可直接复用：**
- InkOS truth files 的 7 文件设计思路
- novelwriter2 world entities 的属性定义
- NovelForge card type schema 格式

**需要改造：**
- 把 InkOS 的 7 个分散 truth files 统一为一个有版本号的 canonical state
- 把 novelwriter2 的 Python 类模型转为 JSON Schema
- 把 NovelForge 的卡片 schema 精简为小说专用子集

**主要风险：** schema 设计不对会导致后续所有模块返工

**验收标准：**
1. Canonical State JSON Schema 通过团队评审
2. World Model schema 能表达：角色状态、关系、时间线、地点、伏笔、信息边界
3. Rules 格式能支持通用/题材/单书三层
4. LLM 接口能支持至少 2 个 provider（Claude + OpenAI）

---

### Phase 1：一致性内核 MVP

**阶段目标：** 实现 canonical state 存储、context assembly、visibility gating、chapter settle、deterministic postcheck。这是整个系统的根基。

**交付物：**
- `novel_runtime/state/canonical.py` — Canonical State 读写
- `novel_runtime/state/world_model.py` — World Model CRUD
- `novel_runtime/state/schema.py` — Schema 校验 + Schema Composer（$ref 解析、$defs 注入、字段保护）
- `novel_runtime/context/assembly.py` — 上下文装配
- `novel_runtime/context/visibility.py` — 可见性裁剪
- `novel_runtime/pipeline/settler.py` — 章节结算
- `novel_runtime/pipeline/postcheck.py` — 确定性检查
- 单元测试 + 集成测试

**涉及模块：** state/, context/, pipeline/settler + postcheck

**可直接复用：**
- novelwriter2 `context_assembly.py`（Aho-Corasick 实体匹配 + token budget 裁剪）
- novelwriter2 `world_visibility.py`（三级可见性）
- novelwriter2 `continuation_postcheck.py`（新名词/称号/漂移检测）
- InkOS settler 的结算逻辑（更新 truth files 的流程）

**需要改造：**
- novelwriter2 的上下文装配需要适配新的 canonical state schema
- InkOS 的 settler 需要从 TypeScript 移植到 Python
- postcheck 规则需要合并三个来源（novelwriter2 + arboris + novel-writer）

**主要风险：**
- Canonical State schema 可能在实际使用中发现不够用，需要迭代
- Context assembly 的 token budget 策略需要根据不同模型调参

**验收标准：**
1. 能创建 world model 并添加角色/地点/关系
2. context assembly 能根据可见性生成 writer/checker 两套不同上下文
3. settler 能在"模拟章节"后正确更新 canonical state
4. postcheck 能拦住：新未注册名词、时间线跳变、未授权出场
5. 所有核心模块测试覆盖率 > 80%

---

### Phase 2：CLI MVP

**阶段目标：** 把 Phase 1 的 Runtime 能力暴露为稳定 CLI 命令。

**交付物：**
- `novel-cli/` 完整包结构
- `novel project init/open/info`
- `novel world entity add/update/show/list`
- `novel world relationship add/list`
- `novel chapter draft/settle/postcheck`
- `novel state show/diff`
- `--json` flag 全局支持
- REPL 模式
- SKILL.md
- TEST.md + 4 层测试

**涉及模块：** novel-cli/ 全部

**可直接复用：**
- CLI-Anything `repl_skin.py`（直接复制并定制）
- CLI-Anything Click 组织模式（group/command/`--json`/error handling）
- CLI-Anything `SKILL.md` 模板
- CLI-Anything 4 层测试 SOP

**需要改造：**
- repl_skin.py 的颜色/branding 定制
- SKILL.md 内容针对小说系统重写

**主要风险：** CLI 命令面设计不对会影响 Skill 编排的灵活性

**验收标准：**
1. `novel --help` 显示完整命令树
2. `novel --json project info` 返回合法 JSON
3. `novel project init && novel world entity add && novel chapter draft && novel chapter settle && novel chapter postcheck` 全流程可跑通
4. REPL 模式可用
5. `pip install -e .` 后 `which novel` 可发现
6. 4 层测试全部通过

---

### Phase 3：共享章节生命周期与双入口生成

**阶段目标：** 把章节生产统一收敛到一条共享生命周期上：无论草稿来自 Novel 内部 provider 执行，还是来自 CLI 指导下的 AI 编程助手执行，只要章节正文与必要结构化输入就绪，都进入同一条 `settle → postcheck → audit → route → revise → approve → snapshot` 主干。Novel 继续保持 **CLI-first**：Runtime 持有业务真相，CLI 持有正式机器接口，Skill 只做编排，不持有业务逻辑。

**交付物：**
- **共享核心（shared core，本阶段主干）**
  - `novel_runtime/pipeline/auditor.py` — 多维审计（返回含 `severity` + `recommended_action` 的结构化 JSON）
  - `novel_runtime/pipeline/reviser.py` — 修订 + AI 守卫
  - `novel_runtime/pipeline/router.py` — Confidence Router（audit 结果→ pass/revise/rewrite/escalate 路由决策）
  - `novel_runtime/state/snapshot.py` — 快照 / 回滚
  - CLI 命令：`novel chapter settle/postcheck/audit/route/revise/approve`、`novel snapshot create/list/diff/rollback`
  - 章节入口归一化与验证约束：无论输入来自 Route A 还是 Route B，最终都要落到同一 canonical state、同一 settle/audit/approve 语义
- **Route A：Novel 内部 provider / API-by-env 执行**
  - `novel_runtime/pipeline/drafter.py` — 内部草稿生成（接入真实 LLM），可逐步演进到 scene-level iteration（plan→write→embellish→memory-update）
  - `novel_runtime/llm/provider.py` — LLM 调用抽象（通过 env / config 解析 provider）
  - `novel_runtime/llm/temperature.py` — 温度策略
  - `novel_runtime/llm/resilience.py` — LLM 韧性层（错误分类、指数退避、优先队列、动态限速、状态追踪）
  - CLI 命令：`novel chapter draft`
  - Route A Skill：围绕已发布 CLI / Runtime 合同编排 Novel 自己执行的生成流程
- **Route B：CLI 指导 + AI 编程助手执行**
  - CLI guidance/export 面：输出结构化 JSON guidance，明确允许操作、所需输入、期望产物、settlement 模板与回传契约
  - AI 编程助手按 guidance 执行具体操作：写正文、生成/整理 JSON、落文件、调用已发布 CLI、收集中间产物与 receipts
  - Route B 回传契约：将正文、settlement、执行结果交回 Novel，由 CLI 统一验证、入库并继续共享生命周期
  - Route B Skill：围绕 guidance → assistant execution → CLI validation 的多步编排，不得藏业务逻辑
- 端到端测试：共享核心至少能承接两类入口中的任意一种完成章节闭环；Route A / Route B 各自都有可验证的能力边界与 Skill 编排方式

**涉及模块：**
- 共享核心：`pipeline/`、`state/snapshot`、`chapter` CLI 生命周期命令
- Route A：`pipeline/drafter.py`、`llm/`（含 resilience）
- Route B：CLI guidance/export、assistant-result / settlement handoff、host-neutral Skill workflow

**可直接复用：**
- InkOS ContinuityAuditor 的审计维度定义（33 维度可选子集）
- InkOS ReviserAgent 的 spot-fix 模式
- InkOS AI 标记守卫逻辑
- InkOS 快照格式
- AI_Gen_Novel plan→write→embellish→memory 循环（作为 Route A 的增强方向）
- NovelGenerator apiResilienceUtils 的错误分类 + 优先队列设计
- newtype-profile Deputy 置信度路由逻辑
- 现有 CLI-first / `--json` / host-neutral Skill 分层与 workflow-spec 设计

**需要改造：**
- InkOS 审计系统从 TypeScript 移植到 Python
- 审计维度可能需要精简（33 维度先做核心子集，如 15-20 维度）
- 快照存储格式需要适配新的 canonical state schema
- Route A 的 drafter/provider/temperature/resilience 从“单一路线假设”改成“共享核心上的一个入口路线”
- Route B 需要补 guidance/export、assistant-result / settlement manifest、CLI 验证与归一化入口
- AI_Gen_Novel 段落级循环如被采用，需要提升到场景级粒度，并保持在 Route A 边界内

**主要风险：**
- Route A 的 LLM 调用质量不稳定（需要多次调参）
- Route B 的 guidance / result contract 漂移，导致 assistant 执行结果难以稳定回收
- 审计结果的分级阈值需要实际校准
- 修订可能引入新问题（AI 守卫是关键防线）
- scene-level iteration 的粒度切分（场景边界识别）需要实际验证
- resilience 层的动态限速参数需要根据不同 provider 调参
- Skill 如果越界持有业务规则，会破坏 CLI-first 的正式合同

**Readiness 术语（Phase 3 官方口径）：**
- **shared-core ready**：只表示共享章节生命周期已可承接章节正文 + 结构化输入，并完成 `settle → postcheck → audit → route → revise → approve → snapshot` 闭环；不自动等于任一路线入口已完成。
- **Route A ready**：只用于 Novel 内部 **provider/API-by-env** 路线；它仅表示 Novel 自己可完成 provider 驱动的草稿生成并接入共享生命周期，**不意味着** REST / network service / MCP 范围。
- **Route B phase 1**：只表示 **CLI guidance + assistant execution + assistant-filled settlement + CLI validation/ingestion** 已成立；它不要求 Route A 先完成。
- **Route B phase 2**：只表示后续的自动提取/自动归一化增强，不属于 Route B phase 1 readiness。
- `chapter draft` 现在对应 Route A 的已落地 provider/API-by-env 草稿入口，连同 resilience 和 packaged verification 一起构成 Route A ready 证据；它**不是** shared-core ready、Route B readiness、或通用 prose-generation readiness 证明，也**不**包含 REST / network service / MCP 范围。

**验收标准：**
1. 共享核心可以承接章节文本与结构化输入，并完成 `settle → postcheck → audit → route → revise → approve → snapshot` 闭环
2. 每章 settle 后 canonical state 正确更新
3. postcheck 能拦住至少 1 个已知错误模式
4. audit 能产出结构化审计报告，含 `severity` 和 `recommended_action` 字段
5. router 能根据 audit 结果自动路由到 pass/revise/rewrite/escalate
6. revise 后 AI 味指标不增（守卫生效）
7. snapshot 能回滚到第 1 章状态
8. Route A 能通过 env / config 配置的 provider 生成真实章节内容，并在 provider 限速时自动退避并恢复
9. Route B 能先由 CLI 输出结构化 guidance，再由 AI 编程助手执行写作/文件/JSON/CLI 操作，并把结果安全交回 Novel 继续生命周期，且不允许直接手改 canonical state
10. Route A 与 Route B 都能通过 CLI 完成正式机器调用；两边 Skill 都只做编排，不需要手动调用 Python，也不持有隐藏业务逻辑

---

### Phase 4：导入既有作品与状态 Bootstrap

**阶段目标：** 支持导入已有小说文本，自动逆向建立 world model 和 canonical state。

**交付物：**
- `novel_runtime/import_export/importer.py` — 文本导入（Markdown / TXT / EPUB）
- `novel_runtime/import_export/bootstrapper.py` — 自动建立 world model
- CLI：`novel import book`、`novel import bootstrap`、`novel import verify`
- 导入测试（至少用 1 本真实小说测试）

**涉及模块：** import_export/

**可直接复用：**
- InkOS 的 import/bootstrap 流程设计
- novelwriter2 的 world model schema 作为 bootstrap 目标

**需要改造：**
- bootstrap 需要 LLM 辅助提取角色/地点/关系/时间线（InkOS 方案）
- 需要人工审核 bootstrap 结果的交互流程

**主要风险：**
- 自动 bootstrap 的准确率取决于 LLM 能力
- 长篇小说的导入可能超 token 限制，需要分段处理

**验收标准：**
1. 能导入 Markdown 格式的小说（至少 10 章）
2. bootstrap 能自动识别主要角色（>80% 召回率）
3. bootstrap 后的 canonical state 通过 postcheck
4. 导入后能从第 11 章继续 draft

---

### Phase 5：审查 / 修订 / 回滚增强

**阶段目标：** 增强审计维度、修订策略、文本审计、去 AI 味。

**交付物：**
- 扩展审计维度到 25+
- `novel inspect text-audit` — 离线文本审计（连接词密度 / AI 套话 / 句长分布）
- `novel inspect style-report` — 风格分析
- `novel_runtime/knowledge/style.py` — 风格指纹 + 锚定
- 三层规则引擎完整实现
- Anti-AI 改写模块

**涉及模块：** pipeline/auditor, rules/, knowledge/style, inspect

**可直接复用：**
- novel-writer `text-audit.sh` 规则（转为 Python 实现）
- novel-writer `check-consistency.sh` 规则
- novel-writer `anti-ai-advanced.md` 规则库
- InkOS 33 维度审计定义（扩展到完整集）
- InkOS 风格克隆 / 指纹

**需要改造：**
- shell 脚本规则转 Python
- 风格指纹算法适配

**主要风险：** 规则过多可能导致误报率上升

**验收标准：**
1. text-audit 能检测：连接词密度 > 阈值、AI 高频句式、段落长度异常
2. style-report 能输出文风指纹摘要
3. 规则引擎支持三层叠加且可禁用单条规则
4. Anti-AI 改写后 AI 味指标下降

---

### Phase 6：Knowledge / KG / Workflow 增强

**阶段目标：** 增加知识图谱、伏笔追踪、RAG 召回等知识层能力。

**交付物：**
- `novel_runtime/knowledge/kg.py` — 知识图谱（角色关系 / 事件链 / 立场变化）
- `novel_runtime/knowledge/foreshadow.py` — 伏笔追踪
- RAG 召回层（向量检索，作为辅助召回，不负责定真）
- `novel state hooks` / `novel state characters` CLI 命令增强

**涉及模块：** knowledge/

**可直接复用：**
- NovelForge 知识图谱设计（双后端：内存 + 持久化）
- InkOS pending_hooks 伏笔追踪
- AI_NovelGenerator 向量检索思路

**需要改造：**
- KG 只取小说相关子集，不需要通用知识图谱
- RAG 需要明确"只负责召回、不负责定真"的边界

**主要风险：** KG 和 RAG 的维护成本较高

**验收标准：**
1. KG 能查询角色间关系并返回结构化数据
2. 伏笔追踪能列出所有未回收伏笔及到期状态
3. RAG 召回的内容不会绕过 visibility gating

---

### Phase 6.5：Agent Session + 可选编排层

**阶段目标：** 实现交互式 agent 会话能力和可选的 Chief/Deputy/Specialist 编排层，为 Skill 层提供更灵活的编排基础设施。

**交付物：**
- `novel_runtime/llm/agent_session.py` — 工具调用式对话会话（React/Tool Agent 模式），支持工具注册、上下文注入、确认机制、配额管理
- `novel_runtime/orchestration/chief.py` — Chief 决策层
- `novel_runtime/orchestration/deputy.py` — Deputy 调度层
- `novel_runtime/orchestration/shared_context.py` — 跨 agent 上下文共享
- `novel_runtime/orchestration/confidence.py` — 置信度路由（与 pipeline/router.py 配合）
- CLI 命令：`novel agent chat`、`novel agent run`、`novel agent status`
- 集成测试：agent session 完成一个完整章节创作流程

**涉及模块：** llm/agent_session, orchestration/

**可直接复用：**
- NovelForge 灵感助手后端的 React/Tool Agent 链路（SSE 流式、工具调度、确认机制）
- newtype-profile Chief/Deputy/Specialist 架构（chief_task 工具、hooks、shared-context artifacts）

**需要改造：**
- NovelForge 助手链路从 FastAPI/SSE 移植到 CLI 友好的会话模式
- newtype-profile 从 TypeScript 移植到 Python
- orchestration 层需要设计为可选叠加层，不影响固定流水线的默认行为

**主要风险：**
- agent 驱动模式的可控性和可预测性不如固定流水线
- orchestration 层增加系统复杂度，需要严格的"可选"边界

**验收标准：**
1. `novel agent chat` 能启动交互式 agent 会话并完成工具调用
2. agent session 支持注册 novel CLI 命令作为可用工具
3. 用户可选择"固定流水线"或"agent 驱动"两种模式
4. orchestration 层不影响默认固定流水线的行为和性能
5. shared_context 能在多步 agent 任务间正确传递上下文

---

### Phase 7：外层 Skill / Plugin / MCP 接入

**阶段目标：** 把 Novel CLI 能力封装为多种外层接口。

**交付物：**
- Claude Code Plugin（`SKILL.md` + 命令映射）
- MCP Server（可选）
- API 文档
- 完整的 Skill 流程定义（新书 / 续写 / 修复 / 导入 / 巡检 / 终章 / 多版本择优 / 雪花创作法 / 番外写作 / 五问启动 / 市场调研 / 写作统计）
- **Skill 层编排规范文档**：明确所有 Skill 必须遵守"纯编排"原则，硬逻辑一律调用 Runtime CLI 返回的结构化 JSON

**涉及模块：** skills/, 外层适配

**可直接复用：**
- CLI-Anything 的 plugin 打包模式
- CLI-Anything 的 SKILL.md 生成器

**主要风险：**
- 外层接口的抽象层可能泄漏 Runtime 复杂度
- Skill 编排中如果不严格遵守"纯编排"原则，可能导致硬编码逻辑泄漏到 prompt 层

**验收标准：**
1. Claude Code 中能通过 Skill 完成：新建项目 → 写 3 章 → 审计 → 快照
2. MCP client 能调用核心命令
3. SKILL.md 能被 agent 正确理解并执行
4. 所有 Skill 流程的条件分支仅依赖 CLI 返回 JSON 中的结构化字段（`recommended_action` / `severity` / `expired` 等），不含内联硬编码逻辑
5. agent 驱动模式可通过 `novel agent chat` 进入，Skill 可调用 agent session 完成复杂交互任务

---

## 八、主要风险与取舍

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Canonical State schema 设计不对 | 后续全部模块返工 | Phase 0 充分评审；Phase 1 先用最小字段集验证 |
| InkOS TypeScript → Python 移植量大 | Phase 1-3 耗时增加 | 只移植核心逻辑，不做全量移植；先做接口再做实现 |
| LLM 调用质量不稳定 | 生成/审计/修订结果波动 | Temperature 分离；resilience 层自动退避；确定性 postcheck 兜底 |
| 规则过多导致误报 | 用户体验差 | 规则分级（blocker/major/minor）；支持禁用单条规则；postcheck whitelist |
| 过度设计 | 交付缓慢 | 每个 Phase 都有明确 MVP 和验收标准；不超前实现 |
| 和源项目的许可证冲突 | 法律风险 | 移植前确认每个源项目的 license；"仅参考思路"的部分重新实现 |
| Scene-level iteration 粒度选择 | 场景边界识别不准导致循环效果差 | 先支持手动标记场景边界，后期再做自动识别；保留章节级 fallback |
| Orchestration 可选层增加复杂度 | 系统行为不可预测 | 严格设计为可选叠加层；默认关闭，需显式启用；固定流水线始终可用 |
| Skill 层编排泄漏硬编码 | 判断逻辑分散在 prompt 和代码中，难以维护 | 强制 Skill 只读取 Runtime 返回的 JSON 结构化字段；Code Review 时检查 Skill 层是否有条件判断 |

### 关键取舍

| 取舍 | 选择 | 原因 |
|------|------|------|
| Python vs TypeScript | Python | novelwriter2 核心模块已是 Python；NLP/数据处理生态更好；CLI-Anything 模式验证过 |
| 文件存储 vs 数据库 | 先文件后 SQLite | 文件简单可 diff 可 git 追踪，MVP 阶段够用 |
| 全量移植 vs 最小移植 | 最小移植 | 先跑通核心路径，再逐步增强 |
| 单 repo vs multi-repo | 单 repo（monorepo） | Runtime + CLI + Skill 紧耦合阶段用 monorepo 效率更高 |
| 33 维度审计 vs 精简子集 | 先 15-20 维度 | 避免早期过度投入审计维度调参 |
| 固定流水线 vs Agent 驱动 | 两者共存，固定流水线为默认 | 固定流水线可控可预测（默认模式）；Agent 驱动灵活但风险高（可选模式）|
| 段落级迭代 vs 场景级迭代 | 场景级 | 段落级太碎，章节级太粗；场景级是质量和效率的平衡点 |

---

## 九、最终推荐的一句话结论

**以 InkOS 的一致性流水线为骨架，以 novelwriter2 的 world model + postcheck 为事实内核，以 NovelForge 的 schema/KG/agent session 为知识层和交互层参考，以 AI_Gen_Novel 的场景级迭代循环提升章内质量，以 newtype-profile 的 Chief/Deputy 架构提供可选编排层，以 NovelGenerator 的 resilience 策略强化 LLM 调用韧性，用 CLI-Anything 的 CLI + SKILL.md 模式打包成 agent 可调用的 headless 小说写作操作系统。先做 Runtime，再做 CLI，最后做 Skill，UI 放最后。**

---

## 十、全量覆盖审查：14 项目功能补漏

> 本次对全部 14 个项目（InkOS、novelwriter2、NovelForge、arboris-novel、novel-writer、Long-Novel-GPT、AI_NovelGenerator、NovelWriter3、NovelGenerator、AI-automatically-generates-novels、chinese-novelist-skill、newtype-profile、AI_Gen_Novel、novelWriter）的 README + `.qoder/repowiki` 做了逐项扫描，对照 v1 架构文档，以下为遗漏功能及其归属判断。

### 10.1 Runtime 层补漏

| 功能模块 | 子功能 | 来源项目 | 必须保留 | 优先级 | 对一致性价值 | 迁移方式 | CLI 可行性 | 适配难度 |
|----------|--------|----------|----------|--------|-------------|----------|-----------|----------|
| **Lore Manager** | Aho-Corasick 关键词索引 + 缓存，按匹配度注入上下文 | novelwriter2(`lore_manager.py`) | ✅ | P0 | 高——精准召回相关设定 | 直接移植（已 Python） | ✅ 内部模块，context assembly 调用 | 低 |
| **Multi-version Generation** | 同章生成 N 个版本，流式输出第一个，其余后台并行 | novelwriter2(continue/stream) + arboris-novel(pipeline_orchestrator) | ✅ | P1 | 中——择优提升单章质量 | 改造后移植 | ✅ `novel chapter draft --versions 3` | 中 |
| **Pacing Controller** | 三幕/英雄之旅/波浪式节奏曲线规划，章节节奏建议，弧线健康验证 | arboris-novel(`pacing_controller.py`) | ✅ | P2 | 中高——避免中后期节奏疲软 | 直接移植（已 Python） | ✅ `novel inspect pacing` | 低 |
| **Reader Simulation** | 模拟多种读者画像（休闲/硬核/情感/刺激/评论家），弃书风险评估 | arboris-novel(`reader_simulator_service.py`) | ⚠️ | P2 | 中——面向商业写作 | 直接移植（已 Python） | ✅ `novel inspect reader-sim` | 低 |
| **Self-Critique Loop** | 6 维度 LLM 批评→修订→再批评循环，加权评分 | arboris-novel(`self_critique_service.py`) | ✅ | P2 | 中高——精细化质量提升 | 直接移植（已 Python） | ✅ `novel chapter critique` | 低 |
| **Enhanced Writing Flow** | 体质/人格/伏笔/派系等增强 prompt 注入 | arboris-novel(pipeline_orchestrator) | ⚠️ | P2 | 中——丰富生成层次 | 仅参考思路 | ✅ 配置化 prompt 模板 | 中 |
| **@DSL Context Injection** | `@角色卡[previous]` 等 DSL 语法精确引用项目数据注入上下文 | NovelForge(`prompt_builder.py`) | ⚠️ | P2 | 中高——精确上下文引用 | 仅参考思路（设计新 DSL） | ✅ prompt 模板内支持 DSL | 中 |
| **Instruction Stream** | 字段级生成（set/append/done），增量解析校验，失败自动重试 | NovelForge(`instruction_generator.py`, `instruction_validator.py`) | ⚠️ | P2 | 中——结构化输出质量 | 仅参考思路 | ✅ Runtime 内部协议 | 高 |
| **Worldpack Import/Export** | 世界模型打包分享，冲突检测，导入规划 | novelwriter2(`worldpack_import.py`) | ⚠️ | P2 | 中——世界设定复用 | 改造后移植 | ✅ `novel world export-pack / import-pack` | 中 |
| **Postcheck Whitelist** | 对已确认的 postcheck 警告加白名单，避免反复误报 | novelwriter2(postcheck whitelist storage) | ✅ | P1 | 高——减少误报噪音 | 直接移植 | ✅ `novel chapter postcheck --whitelist` | 低 |
| **Memory Compression** | 长文本压缩为"前文记忆"摘要，阈值触发更新 | AI_Gen_Novel(`AIGN.py` memory_maker) + AI_NovelGenerator(global_summary) | ✅ | P1 | 高——长篇必备的摘要层 | 改造后移植 | ✅ `novel chapter summarize` | 中 |
| **Validation Levels** | quick / standard / deep 三级验证深度 | novel-writer(`validation-rules.json`) | ✅ | P1 | 中高——灵活控制检查粒度 | 改造后移植 | ✅ `novel chapter postcheck --level deep` | 低 |
| **AIGC Detection Pipeline** | 规则检测 + API 检测 + 历史统计 + 反检测改写循环 | InkOS(`detect` command, detection_history.json) | ✅ | P1 | 高——去 AI 味核心 | 改造后移植 | ✅ `novel detect` | 中 |
| **Confidence Routing** | 审计分数→ pass/polish/rewrite/escalate 路由 | newtype-profile(Deputy 置信度路由) + InkOS(质量门控) | ✅ | P1 | 高——自动化修订决策 | 仅参考思路 | ✅ audit 结果自动路由 | 中 |
| **Coherence Manager** | 跨章世界/角色/剧情一致性追踪 + 自动修复建议 | NovelGenerator(`CoherenceManager`) | ⚠️ | P2 | 中高——补充 postcheck | 仅参考思路 | ✅ `novel state validate --fix-suggest` | 中 |
| **Emotion Curve / Quality Analytics** | 情绪曲线分析、节奏统计、重复检测 | NovelGenerator(`QualityController`) + NovelWriter3(trend tracking) | ⚠️ | P2 | 中——数据化质量评估 | 仅参考思路 | ✅ `novel analytics` | 中 |

### 10.2 CLI 层补漏

| 功能模块 | 子功能 | 来源项目 | 优先级 | 迁移方式 | CLI 可行性 | 适配难度 |
|----------|--------|----------|--------|----------|-----------|----------|
| **Daemon / Scheduler** | 后台守护进程，定时批量写作，并发多书，质量门控暂停 | InkOS(`inkos up/down`) | P2 | 改造后移植（TS→Python） | ✅ `novel daemon start/stop/status` | 高 |
| **Notification** | 章节完成/审计失败通知（Telegram/Feishu/WeChat/Webhook+HMAC） | InkOS(通知系统) | P3 | 改造后移植 | ✅ `novel config notification` | 中 |
| **Analytics** | 审计通过率、高频问题、章节排名、成本追踪 | InkOS(`inkos analytics`) | P2 | 改造后移植 | ✅ `novel analytics [book-id]` | 中 |
| **Doctor / Diagnostics** | 配置诊断、API 连通性测试 | InkOS(`inkos doctor`) | P1 | 参考思路新建 | ✅ `novel doctor` | 低 |
| **Detect** | AIGC 检测 + 统计 + 历史记录 | InkOS(`inkos detect`) | P1 | 改造后移植 | ✅ `novel detect [chapter-id]` | 中 |
| **Style** | 风格分析 + 风格导入 | InkOS(`inkos style analyze/import`) | P2 | 改造后移植 | ✅ `novel style analyze/import` | 中 |
| **Radar / Market Scan** | 市场趋势扫描（Radar Agent） | InkOS(`inkos radar scan`) | P3 | 仅参考思路 | ✅ `novel radar scan` | 中 |
| **Genre Management** | 内置题材模板 CRUD + 自定义 | InkOS(`inkos genre list/show/copy/create`) | P1 | 改造后移植 | ✅ `novel genre list/show/create/copy` | 低 |
| **Multi-model Config** | 按 agent 角色配置不同模型/provider | InkOS(`inkos config set-model`) | P1 | 参考思路新建 | ✅ `novel config set-model <role> <model>` | 低 |
| **Writing Stats** | 写作统计（字数/会话/时间） | novelWriter(sessions.jsonl) | P3 | 仅参考思路 | ✅ `novel stats` | 低 |
| **Chapter Splitter** | 导入时自动拆分章节 | InkOS(`--split` regex) + AI-automatically-generates-novels | P1 | 改造后移植 | ✅ `novel import book --split <regex>` | 低 |
| **Canon / Spinoff Import** | 番外写作模式，母本导入 + 4 专用审计维度 | InkOS(`inkos import canon`) | P2 | 改造后移植 | ✅ `novel import canon <parent-book>` | 中 |
| **Prompt Template Management** | 可编辑的 prompt 模板/工坊 | NovelForge(Prompt Workshop) | P2 | 仅参考思路 | ✅ `novel prompt list/show/edit` | 中 |
| **Export Formats** | EPUB / PDF / DOCX / ODT / HTML 多格式导出 | novelWriter(export pipeline) + NovelGenerator | P2 | 参考思路新建 | ✅ `novel project export --format epub` | 中 |

### 10.3 Skill 层补漏

| 功能模块 | 说明 | 来源参考 | 优先级 |
|----------|------|----------|--------|
| **多版本择优流程** | draft N versions → compare → select → approve | arboris-novel + novelwriter2 | P2 |
| **雪花创作法流程** | 标签→金手指→梗概→大纲→世界观→蓝图→分卷→角色→场景→章节 | NovelForge(内置工作流) | P2 |
| **市场调研流程** | radar scan → trend analyze → genre select → outline adjust | InkOS(Radar Agent) | P3 |
| **番外写作流程** | import canon → setup parent refs → draft spinoff → spinoff audit (4 dims) | InkOS | P2 |
| **五问启动流程** | 5 问采集需求 → 大纲确认 → 人设确认 → 开始创作 | chinese-novelist-skill | P2 |
| **写作统计流程** | 追踪字数/进度/成本 → 生成统计报告 | novelWriter + InkOS(analytics) | P3 |

### 10.4 各项目功能覆盖完整性审查

下表标记每个项目的核心功能在当前架构 v1 中的覆盖状态（✅ 已覆盖 / 🔧 本次补入 / ❌ 不纳入 + 原因）：

| 项目 | 核心功能 | 状态 | 说明 |
|------|----------|------|------|
| **InkOS** | 5-Agent 流水线 | ✅ | pipeline/ 覆盖 |
| | 7 truth files | ✅ | canonical state |
| | 33 维度审计 | ✅ | auditor |
| | 11 条写后硬规则 | ✅ | postcheck |
| | 两阶段写作 + 温度分离 | ✅ | temperature.py |
| | AI 标记守卫 | ✅ | reviser |
| | 快照/回滚 | ✅ | snapshot |
| | 风格分析/导入 | ✅ | style.py |
| | 守护进程/调度 | 🔧 | daemon |
| | 通知推送 | 🔧 | notification (P3) |
| | AIGC 检测 + 统计 | 🔧 | detect command |
| | Analytics | 🔧 | analytics command |
| | Doctor 诊断 | 🔧 | doctor command |
| | Genre 模板系统 | 🔧 | genre command |
| | Multi-model routing | 🔧 | config set-model |
| | Radar 市场扫描 | 🔧 | radar (P3) |
| | Canon/Spinoff 导入 | 🔧 | import canon |
| | Chapter split regex | 🔧 | import --split |
| **novelwriter2** | World Model + visibility | ✅ | world_model + visibility |
| | Context Assembly (Aho-Corasick) | ✅ | assembly.py |
| | Continuation Postcheck | ✅ | postcheck.py |
| | Bootstrap pipeline | ✅ | bootstrapper.py |
| | Style anchor | ✅ | style.py |
| | Lore Manager | 🔧 | 归入 context/ |
| | Worldpack import/export | 🔧 | world export-pack/import-pack |
| | Multi-version generation | 🔧 | chapter draft --versions |
| | Postcheck whitelist | 🔧 | postcheck --whitelist |
| | Streaming generation | 🔧 | Runtime 内部实现 |
| **NovelForge** | Card/Schema system | ✅ | schema.py |
| | Knowledge Graph | ✅ | kg.py |
| | Workflow Engine | ✅ Skill 层 | Skill 编排 |
| | @DSL 上下文注入 | 🔧 | prompt DSL 参考 (P2) |
| | Instruction stream | 🔧 | 参考思路 (P2) |
| | Prompt Workshop | 🔧 | prompt management (P2) |
| | 审核系统 + 质量门禁 | ✅ | audit + rules |
| | 灵感助手 | 🔧 | 后端有完整 React/Tool Agent 链路，纳入为 agent session 能力 (P2) |
| | Schema Studio | 🔧 | 后端有 Schema 合成/$ref 解析/$defs 注入，纳入 schema.py 增强 (P2) |
| **arboris-novel** | Pipeline orchestrator | ✅ | pipeline/ |
| | Chapter guardrails | ✅ | postcheck |
| | Writer context builder | ✅ | visibility + assembly |
| | Pacing controller | 🔧 | inspect pacing (P2) |
| | Self-critique (6维) | 🔧 | chapter critique (P2) |
| | Reader simulation | 🔧 | inspect reader-sim (P2) |
| | Multi-version + AI review | 🔧 | multi-version generation |
| | Enhanced writing flow | 🔧 | 参考思路 |
| | Memory layer service | ✅ | context assembly |
| **novel-writer** | text-audit.sh | ✅ | inspect text-audit |
| | check-consistency.sh | ✅ | state validate |
| | anti-ai-advanced 规则库 | ✅ | rules/ |
| | validation-rules.json (3 级) | 🔧 | validation levels |
| | Plugin system | 🔧 | 参考思路→prompt templates (P2) |
| | Tracking templates | ✅ | canonical state 覆盖 |
| | Slash command framework | ✅ | CLI + Skill 覆盖 |
| **Long-Novel-GPT** | Multi-layer writer cascade | 🔧 | 参考思路→outline→plot→draft 层级 |
| | Review → rewrite loop | ✅ | audit → revise |
| | Chunk mapping / diff | 🔧 | 参考思路 (P2) |
| | SSE streaming + cost | 🔧 | Runtime streaming support |
| **AI_NovelGenerator** | Vector RAG (ChromaDB) | ✅ | kg.py + RAG (P2) |
| | Global summary + character state | ✅ | canonical state + settler |
| | Chapter finalization | ✅ | settler |
| | Consistency checker | ✅ | audit |
| **NovelWriter3** | Multi-level review | ✅ | audit 多维度 |
| | File-based persistence | ✅ | JSON 文件存储 |
| | Genre-specific generators | 🔧 | genre 模板 |
| | Quality trend tracking | 🔧 | analytics (P2) |
| **NovelGenerator** | StoryContextDatabase | ✅ | canonical state 覆盖 |
| | CoherenceManager | 🔧 | state validate --fix-suggest |
| | QualityController (emotion/pacing) | 🔧 | analytics + pacing |
| | Export (EPUB/PDF) | 🔧 | export formats |
| | API resilience | 🔧 | 含错误分类/优先队列/动态限速/状态追踪，纳入 llm/resilience.py (P1) |
| **AI-automatically-generates-novels** | Knowledge base panel | ✅ | world model |
| | AI scoring + iterative rewrite | ✅ | audit + revise loop |
| | Anti-AI rewrite (去AI味) | ✅ | detect + revise |
| | Mind-map visualization | ❌ | UI 功能 |
| | Prompt editor with variables | 🔧 | prompt template management |
| | Chapter splitter | 🔧 | import --split |
| **chinese-novelist-skill** | 12-point quality checklist | ✅ | rules + audit |
| | Consistency documents | ✅ | canonical state |
| | Three-phase chapter workflow | ✅ | Skill 层 |
| | Five-question intake | 🔧 | Skill 层五问流程 |
| | check_chapter_wordcount.py | ✅ | postcheck 覆盖 |
| **newtype-profile** | Chief/Deputy/Specialist 架构 | 🔧 | 模块化框架，纳入为可选编排层 orchestration/ (P2) |
| | Quality scoring + confidence routing | 🔧 | confidence routing |
| | Shared context artifacts | ✅ | context assembly |
| | Archivist knowledge management | ✅ | canonical state + knowledge/ |
| | Cross-session memory | ✅ | 文件持久化 |
| **AI_Gen_Novel** | Memory compression (memory_maker) | 🔧 | chapter summarize |
| | RecurrentGPT iterative paragraph | 🔧 | plan→write→embellish→memory 循环适配到场景级，纳入 drafter.py (P1) |
| | Per-agent temperature | ✅ | temperature.py |
| | novel_record.md logging | ✅ | audit report + snapshot |
| **novelWriter** | Rich editor markup | ❌ | headless 系统不需要编辑器 |
| | Project tree structure | ✅ | project 数据模型 |
| | Writing statistics | 🔧 | stats command (P3) |
| | Backup/restore | ✅ | snapshot 覆盖 |
| | Tag system (@tag/@pov/@char) | 🔧 | 参考→实体引用语法 |
| | Index system | ✅ | canonical state 索引 |
| | Multi-format export | 🔧 | export formats |
| | Spell-checking | ❌ | 中文小说无需拼写检查 |

### 10.5 CLI 适配可行性总评

| 评估维度 | 结论 |
|----------|------|
| **核心流水线 CLI 化** | ✅ 完全可行。draft/settle/postcheck/audit/revise/snapshot 都是明确的原子操作，天然适合 CLI |
| **状态查询 CLI 化** | ✅ 完全可行。state/world/hooks/timeline 都是只读查询，JSON 输出友好 |
| **导入/导出 CLI 化** | ✅ 完全可行。文件操作天然适合 CLI |
| **守护进程 CLI 化** | ⚠️ 需要额外设计。daemon start/stop/status 需要进程管理（可参考 InkOS 的 `up/down`），适配难度中等 |
| **多版本生成 CLI 化** | ✅ 可行。`--versions N` flag，输出 JSON 数组，人工或自动择优 |
| **通知系统 CLI 化** | ✅ 可行。`novel config notification --webhook <url>` 配置即可 |
| **分析/统计 CLI 化** | ✅ 完全可行。analytics/stats 输出表格或 JSON |
| **节奏/读者模拟 CLI 化** | ✅ 可行。输出结构化报告 |
| **AIGC 检测 CLI 化** | ✅ 完全可行。输入文本，输出检测结果 + 统计 |
| **Prompt 模板管理 CLI 化** | ✅ 可行。list/show/edit（edit 可打开编辑器） |
| **Agent Session CLI 化** | ✅ 可行。`novel agent chat` 启动交互会话，`novel agent run` 运行非交互任务 |
| **整体适配难度评估** | **低-中**。绝大多数功能天然适合 CLI，只有 daemon/scheduler 和 streaming 需要额外工程量 |

### 10.6 v1 判断修正：原"不纳入"项重新评估

> 以下是 v1 中标记为 ❌ 不纳入的功能，经二次调查后的修正。

| 原判断 | 功能 | 修正后 | 修正原因 | 归属层 | 优先级 |
|--------|------|--------|----------|--------|--------|
| ❌ NovelForge 灵感助手 | 对话式工具调用 + 上下文注入 + 卡片 CRUD | 🔧 **纳入** | 后端有完整 React/Tool Agent 链路（SSE 流式、工具调度、确认机制、配额管理），headless 下可作为"交互式 agent 会话"能力 | Runtime: `llm/agent_session.py` + CLI: `novel agent chat` | P2 |
| ❌ NovelForge Schema Studio | Schema 合成 + $ref 解析 + $defs 注入 + 工作流联动 | 🔧 **纳入** | 后端有 `schema_service.py` 做 Schema 组装、引用解析、字段保护、卡片类型联动，这是 World Model Schema 校验的增强能力 | Runtime: `state/schema.py` 增强 | P2 |
| ❌ AI_Gen_Novel 段落级迭代 | plan→write→embellish→memory-update 循环 | 🔧 **纳入** | 该循环可适配到场景/节级粒度：plan/temp_setting 作为场景级 storyboard，embellisher 做场景级润色，memory_maker 做场景级摘要压缩。对章内质量提升有直接价值 | Runtime: `pipeline/drafter.py` 内部支持 scene-level iteration | P1 |
| ❌ newtype-profile Agent 框架 | Chief/Deputy/Specialist 编排 | 🔧 **纳入（可选层）** | 框架是模块化的（chief_task 工具 + hooks + shared-context artifacts + confidence routing），可作为"可选编排层"叠加在固定流水线之上。用户可选择：固定流水线（默认）或 agent 驱动灵活流水线 | Runtime: `orchestration/` 新模块（可选） + CLI: `novel agent` 命令组 | P2 |
| ❌ NovelGenerator API resilience | 错误分类 + 优先队列 + 动态限速 + 状态追踪 | 🔧 **纳入** | 不是简单 retry，有 error classification、priority queue、dynamic rate control、recovery estimation。这些是 LLM 抽象层的必要能力 | Runtime: `llm/resilience.py` | P1 |
| ❌ novelWriter 拼写检查 | Enchant 集成 | ❌ **维持不纳入** | 中文小说场景下拼写检查价值极低，且 Enchant 对中文支持差 | — | — |

### 10.7 Skill 层硬编码审查

> 原则：Skill 层只应包含"纯编排逻辑"（调用顺序、条件分支、策略选择），不应包含任何硬编码的业务规则或数据处理。如果一个流程中有硬编码逻辑，该逻辑必须下沉到 Runtime 或 CLI。
>
> **进一步结论：** 这 14 个来源项目大多形成于 pre-skill 时代，主流实现形态是硬编码系统、CLI、Web 或桌面应用，而不是 skill-native 设计。因此不应把“来源项目里的流程”直接视为 Skill；只有其中可解耦的流程外壳（prompt 模板、提问步骤、人工审批节点、多命令编排）才适合抽成 Skill。

| Skill 流程 | 是否含硬编码 | 审查结论 |
|------------|-------------|----------|
| **新书启动流程** | ❌ 纯编排 | ✅ 适合 Skill。只是 init→world→outline→approve 的调用顺序 |
| **章节续写流程** | ⚠️ 含条件分支逻辑 | ⚠️ 条件分支（audit 失败→revise 还是 rewrite）的**判断规则**必须在 Runtime 的 confidence routing 中实现，Skill 只负责调用 `novel chapter audit` 并根据返回的 JSON 中的 `action` 字段决定下一步 |
| **一致性修复流程** | ⚠️ 含诊断逻辑 | ⚠️ "identify drift"的检测逻辑必须在 Runtime 的 `state validate` 中实现，Skill 只调用并根据结果编排 |
| **导入旧书流程** | ❌ 纯编排 | ✅ 适合 Skill |
| **风格迁移流程** | ❌ 纯编排 | ✅ 适合 Skill |
| **伏笔巡检流程** | ⚠️ 含到期判断 | ⚠️ 伏笔到期判断必须在 Runtime 的 `foreshadow.py` 中实现，Skill 只调用 `novel state hooks --check-expiry` |
| **审查重写流程** | ⚠️ 含分级逻辑 | ⚠️ blocker/major/minor 分级必须在 Runtime 的 auditor 中实现，Skill 只根据返回的级别决定走 batch-revise 还是 rewrite |
| **终章收束流程** | ⚠️ 含弧线验证 | ⚠️ 弧线完整性验证必须在 Runtime 中实现，Skill 只调用并编排 |
| **批量质量审计** | ❌ 纯编排 | ✅ 适合 Skill。只是对多章循环调用 text-audit |
| **多版本择优流程** | ❌ 纯编排 | ✅ 适合 Skill |
| **雪花创作法流程** | ❌ 纯编排 | ✅ 适合 Skill。只是 NovelForge 工作流的步骤顺序 |
| **番外写作流程** | ❌ 纯编排 | ✅ 适合 Skill |
| **五问启动流程** | ❌ 纯编排 | ✅ 适合 Skill |

**结论：6 个 Skill 流程含条件/判断逻辑，这些逻辑的硬编码部分必须下沉到 Runtime，Skill 只负责读取 Runtime 返回的结构化结果并据此编排。换句话说：Skill 负责“流程外壳”，Runtime/CLI 负责“功能本体”。** 具体需要确保：

1. `novel chapter audit` 返回 JSON 必须包含 `recommended_action: "pass" | "revise" | "rewrite" | "escalate"` — **confidence routing 在 Runtime 实现**
2. `novel state validate` 返回 JSON 必须包含 `drift_items: [...]` 和 `fix_suggestions: [...]` — **诊断逻辑在 Runtime 实现**
3. `novel state hooks --check-expiry` 返回 JSON 必须包含 `expired: [...]` 和 `at_risk: [...]` — **到期判断在 Runtime 实现**
4. `novel chapter audit` 返回的每个 issue 必须有 `severity: "blocker" | "major" | "minor"` — **分级在 Runtime 实现**

### 10.7.1 prompts-assets 与 Skill 的边界

> Skill 不是 prompt/模板的总仓库。对于来源项目中的问卷、题材模板、审计 rubric、风格说明、workflow 文案、示例输入输出，更合理的归宿是 `prompts-assets` 层。Skill 可以引用这些资产，但不应把它们与条件分支、状态判断、规则执行混写在一起。换句话说：**Skill 负责“怎么串起来”，prompts-assets 负责“拿什么文案来串”。**

### 10.8 新增 Runtime 模块：因修正而需要补充的

| 新增模块 | 路径 | 说明 | 来源 |
|----------|------|------|------|
| **Agent Session** | `novel_runtime/llm/agent_session.py` | 工具调用式对话会话（React/Tool Agent 模式），支持工具注册、上下文注入、确认机制 | NovelForge 灵感助手 |
| **LLM Resilience** | `novel_runtime/llm/resilience.py` | 错误分类、指数退避、优先队列、动态限速、状态追踪、恢复估算 | NovelGenerator apiResilienceUtils |
| **Scene-level Iteration** | `novel_runtime/pipeline/drafter.py` 内部 | plan→write→embellish→memory-update 场景级循环 | AI_Gen_Novel AIGN.py |
| **Orchestration (可选)** | `novel_runtime/orchestration/` | Chief/Deputy/Specialist 可选编排层，叠加在固定流水线之上 | newtype-profile |
| **Schema Composer** | `novel_runtime/state/schema.py` 增强 | $ref 解析、$defs 注入、卡片类型联动、字段保护 | NovelForge schema_service |
| **Confidence Router** | `novel_runtime/pipeline/router.py` | audit 结果→ pass/revise/rewrite/escalate 路由决策 | newtype-profile + InkOS |

### 10.9 CLI-Anything 7 阶段 SOP 对 Novel Runtime 的适配性评估

> 背景：CLI-Anything 的 HARNESS.md 定义了一套 7 阶段 SOP（标准作业程序），原始设计目标是"把一个已有的 GUI 软件打包成 agent 可用的 CLI"。用户希望将 CLI-Anything 安装为 Claude Code plugin，直接用其 SOP 流程驱动 novel-cli 的开发。本节严谨评估这条路径的可行性。

#### 10.9.1 核心假设差异

CLI-Anything HARNESS.md 的 Phase 1 开篇即明确了五个前提假设：

| # | HARNESS 假设 | Novel Runtime 实际情况 | 差异程度 |
|---|-------------|----------------------|----------|
| 1 | "Identify the backend engine — Most GUI apps separate presentation from logic" | 没有单一 GUI 应用，没有现成后端引擎。Runtime 是从 14 个开源项目整合新建的 | **根本性差异** |
| 2 | "Map GUI actions to API calls — Every button click corresponds to a function call" | 没有 GUI 动作可映射。所有业务逻辑（canonical state、pipeline、audit）需要从零设计 | **根本性差异** |
| 3 | "Identify the data model — What file formats does it use?" | 数据模型需要自行设计（JSON/YAML canonical state），不是从现有软件中提取 | **根本性差异** |
| 4 | "Find existing CLI tools — Many backends ship their own CLI" | 没有现成 CLI 可复用。14 个来源项目各有不同的接口形式 | **根本性差异** |
| 5 | "Catalog the command/undo system" | 没有现成的 undo 系统可暴露。需要自建 snapshot/rollback 机制 | **根本性差异** |

**结论：Phase 1 的全部 5 个假设在 Novel Runtime 场景下均不成立。** 这不是"微调"能解决的，而是 SOP 的起点假设与项目性质的根本错配。

#### 10.9.2 逐阶段适配性矩阵

| 阶段 | HARNESS 原始目标 | 对 Novel Runtime 的适用性 | 判定 | 适配方案 |
|------|-----------------|-------------------------|------|----------|
| **Phase 1: 分析** | 分析已有 GUI 软件的后端、API、数据模型 | ❌ 不适用 | **需重写** | 替换为"多来源功能审计"：分析 14 个来源项目的可移植功能、数据模型、接口形式 → 即本文档第三节已完成的工作 |
| **Phase 2: CLI 架构设计** | REPL + 子命令、命令分组、状态模型、输出格式 | ✅ 直接适用 | **可直接用** | 命令分组、`--json` flag、REPL 模式、状态模型设计 → 本文档第五节已按此模式设计 |
| **Phase 3: 实现** | 数据层→探针→变更→后端集成→渲染→会话→REPL | ⚠️ 部分适用 | **需适配** | "数据层→探针→变更→会话→REPL"可用；"后端集成"需替换为"Runtime 核心模块实现"；"渲染/导出"需替换为"LLM 调用 + 文本生成" |
| **Phase 4: 测试规划** | TEST.md 结构化测试计划 | ✅ 直接适用 | **可直接用** | TEST.md 格式、测试清单、场景规划完全可沿用 |
| **Phase 5: 测试实现** | 4 层测试（unit / e2e-native / e2e-backend / subprocess） | ⚠️ 需适配 | **需适配** | unit ✅ / e2e-native ✅ / e2e-backend 需重定义为"LLM 集成测试"（mock + 真实 API 两层）/ subprocess ✅ |
| **Phase 6: 测试文档** | TEST.md Part 2 追加结果 | ✅ 直接适用 | **可直接用** | 格式和流程完全可沿用 |
| **Phase 6.5: SKILL.md** | 自动提取 CLI 元数据生成技能定义 | ✅ 直接适用 | **可直接用** | skill_generator.py 可直接对 novel-cli 运行 |
| **Phase 7: 发布** | PEP 420 + console_scripts + pip install | ✅ 直接适用 | **可直接用** | 打包模式完全可沿用 |

**总结：8 个阶段中，4 个直接可用，2 个需适配，1 个需完全重写，1 个（Phase 3）需要大幅改造。**

#### 10.9.3 HARNESS.md 核心原则的适用性

| 原则 | HARNESS 原文 | 对 Novel Runtime 的适用性 |
|------|-------------|-------------------------|
| "Use the Real Software — Don't Reimplement It" | **不适用。** Novel Runtime 没有"真实软件"可调用。Runtime 本身就是"真实软件"，需要从零实现 |
| "The Rendering Gap" | **不适用。** 没有渲染管线，不存在"中间文件→真实软件渲染"的模式 |
| "No graceful degradation" | **部分适用。** LLM provider 是硬依赖（类似 HARNESS 中的"真实软件"），但 LLM 不可用时应有离线模式（纯规则检查、状态查询等仍可工作） |
| "Four test layers" | **适用但需重定义。** 第三层"true backend E2E"需从"调用真实 GUI 软件"改为"调用真实 LLM API" |
| "Stateful REPL + Subcommand dual mode" | **完全适用。** |
| "Agent-native --json output" | **完全适用。** |
| "Session file locking" | **完全适用。** |
| "ReplSkin unified experience" | **完全适用。** |

#### 10.9.4 "安装为 Claude Plugin 直接调用"是否可行？

**可行，但不是"开箱即用"，而是"参考使用"。**

CLI-Anything 作为 Claude Code plugin 安装后，提供的是：
1. `/cli-anything <software-path>` 命令 — 触发 7 阶段 SOP
2. `/cli-anything:validate` — 验证已生成 CLI 的结构合规性
3. HARNESS.md 方法论文档 — agent 可读取并遵循
4. repl_skin.py — 可直接复制使用
5. skill_generator.py — 可直接对生成的 CLI 运行

**问题在于：**

| 功能 | 能否直接用 | 原因 |
|------|-----------|------|
| `/cli-anything` 触发构建 | ⚠️ 不能直接用 | 它会按 HARNESS Phase 1 去"分析已有 GUI 软件"，但我们没有 GUI 软件可分析 |
| `/cli-anything:validate` | ✅ 可以用 | 验证目录结构、命名规范、测试覆盖等，这些与业务无关 |
| HARNESS.md 作为参考 | ✅ 可以用 | Phase 2-7 的方法论可作为开发指南 |
| repl_skin.py | ✅ 可以用 | 直接复制到 novel-cli/utils/ |
| skill_generator.py | ✅ 可以用 | CLI 完成后直接运行生成 SKILL.md |
| 4 层测试 SOP | ⚠️ 需适配 | 第三层需重定义 |

#### 10.9.5 推荐操作路径

**不建议：** 安装 CLI-Anything plugin 后直接执行 `/cli-anything` 命令来驱动 novel-cli 开发。原因是 Phase 1 的假设不成立，agent 会尝试去"找后端引擎"和"映射 GUI 动作"，这会浪费时间并产生错误方向。

**建议：** 采用"选择性借用"模式——

```
推荐操作路径：

1. 安装 CLI-Anything plugin（获取 validate 命令和工具链）
2. 跳过 Phase 1（已由本文档第三节"全量功能要素图"替代）
3. Phase 2 CLI 架构设计 → 已由本文档第五节完成
4. Phase 3 实现 → 按本文档 Roadmap 执行，但遵循 HARNESS 的实现顺序建议：
   a. 先做数据层（canonical state / world model / schema）
   b. 再做探针命令（state show / world show / inspect）
   c. 再做变更命令（chapter draft / settle / world entity add）
   d. 再做 Runtime 核心（pipeline / rules / audit）← 替代"后端集成"
   e. 再做会话管理（session / snapshot）
   f. 最后做 REPL（repl_skin.py 直接移植）
5. Phase 4-6 测试 → 遵循 HARNESS 的 TEST.md 规范
6. Phase 6.5 → 用 skill_generator.py 生成 SKILL.md
7. Phase 7 → 按 HARNESS 的打包规范发布
8. 开发过程中用 /cli-anything:validate 检查结构合规性
```

#### 10.9.6 是否需要先改造 CLI-Anything？

**不需要。** 理由：

| 方案 | 工作量 | 收益 | 判断 |
|------|--------|------|------|
| A. 改造 CLI-Anything 使其支持"新建型"项目 | 高（需重写 Phase 1、修改 HARNESS.md、新增模板） | 中（只有 novel-cli 一个用户） | ❌ 投入产出比差 |
| B. 把 CLI-Anything 解耦成 skills 再使用 | 高（需要重构插件架构） | 低（当前架构已够用） | ❌ 过度工程 |
| C. 直接选择性借用，不改造 | 零 | 高（立即可用的部分直接用，不适用的跳过） | ✅ **推荐** |

**一句话：CLI-Anything 是一把好锤子，但我们的项目不全是钉子。拿它能敲的部分来敲（Phase 2/4/5/6/6.5/7 + 工具链），不能敲的部分（Phase 1 + 后端集成假设）自己解决。不需要为了一个项目去改造锤子本身。**

#### 10.9.7 具体落地方案：三层借用架构

"选择性借用"的实操落地分三层，每层解决不同问题：

```
┌──────────────────────────────────────────────────────────┐
│  第三层：novel-cli（最终产物）                              │
│  用户/agent 实际使用的小说写作 CLI                          │
│  ← 这是我们要建的东西，架构文档已设计完毕                    │
├──────────────────────────────────────────────────────────┤
│  第二层：novel-dev-sop Skill（开发过程指导）                │
│  Claude 在开发 novel-cli 时调用的 SOP 技能                 │
│  ← 从 CLI-Anything 方法论适配而来的新 Skill                │
├──────────────────────────────────────────────────────────┤
│  第一层：工具文件复制（一次性迁移）                          │
│  repl_skin.py / skill_generator.py / 模板 / 校验脚本       │
│  ← 从 CLI-Anything 直接复制，不依赖框架                    │
└──────────────────────────────────────────────────────────┘
```

##### 第一层：工具文件复制（一次性，无需 Skill）

| 源文件 | 目标路径 | 用途 | 是否需要改动 |
|--------|---------|------|-------------|
| `CLI-Anything/cli-anything-plugin/repl_skin.py` | `novel/tools/repl_skin.py` | REPL 交互界面（banner、提示符、彩色输出、历史记录） | 微调：改 banner 文本、skill path |
| `CLI-Anything/cli-anything-plugin/skill_generator.py` | `novel/tools/skill_generator.py` | CLI 完成后自动生成 SKILL.md | 微调：模板路径 |
| `CLI-Anything/cli-anything-plugin/templates/SKILL.md.template` | `novel/tools/templates/SKILL.md.template` | SKILL.md 的 Jinja2 模板 | 按需修改章节 |
| `CLI-Anything/cli-anything-plugin/verify-plugin.sh` | `novel/tools/verify-structure.sh` | CI 中校验目录结构完整性 | 改检查项 |

这些文件**独立可用**，不依赖 CLI-Anything 框架，复制即生效。

##### 第二层：创建 `novel-dev-sop` Skill（核心——开发过程工具）

**为什么需要这个 Skill？**

单纯复制文件只解决了"拿到工具"，但没有解决"开发过程中 agent 怎么知道下一步该干什么"。CLI-Anything 的 HARNESS.md 本质是一套**开发方法论**——告诉 agent "第一步做什么、第二步做什么、每一步的验收标准是什么"。这个方法论的价值不在于它的代码，而在于它的**流程编排知识**。

把这个适配后的方法论编码成一个 Skill，Claude 在开发 novel-cli 时就可以随时调用它来获取指导。当前抽取出的通用 Skill 位于 `C:\Users\daixu\.claude\skills\cli-dev-sop\SKILL.md`，Novel 侧消费者实例保留在 `E:\github\novel\skills\novel-dev-sop\SKILL.md`。

**`novel-dev-sop` Skill 的内容结构：**

```yaml
# novel-dev-sop/SKILL.md
---
name: "novel-dev-sop"
description: "Novel Runtime 开发 SOP —— 基于 CLI-Anything 方法论适配"
---
```

Skill 包含以下阶段指导（对应 HARNESS 的适配版本）：

| Skill 阶段 | 对应 HARNESS | 做什么 | 验收标准 |
|------------|-------------|--------|----------|
| `sop:audit` | Phase 1（重写） | 不是"分析 GUI 软件"，而是"审查 14 个来源项目的功能清单" | ✅ 已由本文档第三节完成 |
| `sop:design` | Phase 2（直接用） | CLI 命令树设计、状态模型设计、输出格式约定 | ✅ 已由本文档第五节完成 |
| `sop:implement` | Phase 3（适配版） | 按顺序实现：① schema/state → ② 探针命令 → ③ 变更命令 → ④ Runtime 核心 → ⑤ 会话/快照 → ⑥ REPL | 每步有对应的 pytest 通过 |
| `sop:test-plan` | Phase 4（直接用） | 编写 TEST.md 测试计划 | TEST.md 包含测试清单 + 场景描述 |
| `sop:test-run` | Phase 5（适配版） | 4 层测试：unit / e2e-native / e2e-llm（替代 e2e-backend）/ subprocess | 全部通过 |
| `sop:test-doc` | Phase 6（直接用） | 将测试结果追加到 TEST.md | TEST.md 包含通过率和覆盖报告 |
| `sop:skill-gen` | Phase 6.5（直接用） | 运行 skill_generator.py 生成 SKILL.md | SKILL.md 存在且格式正确 |
| `sop:publish` | Phase 7（直接用） | PEP 420 + console_scripts + pip install -e . | `novel --help` 可执行 |
| `sop:validate` | 新增 | 运行 verify-structure.sh 校验目录/文件完整性 | 校验脚本零报错 |

**这个 Skill 和 CLI-Anything plugin 的区别：**

| 维度 | 安装 CLI-Anything plugin | 创建 novel-dev-sop Skill |
|------|------------------------|------------------------|
| 来源 | CLI-Anything 整体安装 | 新建，仅引用适配后的方法论 |
| Phase 1 | 会去"分析 GUI 软件"（❌ 不适用） | 替换为"功能审计"（✅ 已完成） |
| Phase 3 后端集成 | 假设有外部软件后端 | 替换为"Runtime 核心实现" |
| Phase 5 E2E 测试 | 假设可调用真实 GUI 软件 | 替换为 LLM 集成测试 |
| 依赖 | 依赖 CLI-Anything 框架 | 零依赖，独立 Skill |
| 维护 | 随 CLI-Anything 更新 | 我们自己控制 |

**关键认知：这不是"解耦 CLI-Anything"，而是"从方法论中萃取 + 适配后创建新 Skill"。** CLI-Anything 原封不动，我们只是从它的经验中学习并编码成自己的工具。

##### 第三层：novel-cli 最终产物

这就是本架构文档设计的 CLI 本身（第五节/第十一节的命令树），是用户和 agent 最终使用的工具。第一层提供了构建它的脚手架文件，第二层提供了构建它的过程指导。

##### 操作时间线

```
Phase 0（准备）
├── 复制第一层工具文件到 novel 项目
├── 创建 novel-dev-sop Skill（编写 SKILL.md）
└── 验证 Skill 可被 Claude Code 加载

Phase 1-7（开发）
├── 每个阶段开始前：调用 novel-dev-sop 获取该阶段的指导
├── 每个阶段完成后：调用 sop:validate 检查交付物
└── 重复直到 novel-cli 完整可用

Phase 8（收尾）
├── 运行 sop:skill-gen 生成 novel-cli 自身的 SKILL.md
├── 运行 sop:publish 发布
└── novel-dev-sop 的历史使命完成（可归档）
```

---

## 十一、更新后的 CLI 命令树（完整版）

```
novel
├── project
│   ├── init              # 初始化新项目
│   ├── open              # 打开已有项目
│   ├── info              # 显示项目信息
│   ├── config            # 项目配置（模型、温度、规则集等）
│   │   ├── set           # 设置配置项
│   │   ├── get           # 查看配置项
│   │   ├── set-model     # 按角色配置模型（writer/auditor/reviser 可用不同模型）
│   │   └── notification  # 配置通知渠道
│   └── export            # 导出项目（EPUB / Markdown / DOCX / PDF）
│       └── --format      # 指定格式
│
├── world
│   ├── create            # 创建世界设定
│   ├── show              # 显示世界状态
│   ├── update            # 更新世界设定
│   ├── entity
│   │   ├── add           # 添加实体（角色/地点/物品/势力）
│   │   ├── update        # 更新实体属性
│   │   ├── show          # 显示实体详情
│   │   ├── list          # 列出所有实体
│   │   └── delete        # 删除实体
│   ├── relationship
│   │   ├── add           # 添加关系
│   │   ├── update        # 更新关系
│   │   ├── list          # 列出关系
│   │   └── graph         # 显示关系图（文本格式）
│   ├── export-pack       # 导出 Worldpack（可分享的世界设定包）
│   └── import-pack       # 导入 Worldpack（含冲突检测）
│
├── outline
│   ├── generate          # 生成大纲
│   ├── show              # 显示大纲
│   ├── update            # 更新大纲节点
│   └── approve           # 确认大纲
│
├── chapter
│   ├── draft             # 生成章节草稿
│   │   ├── --versions N  # 生成 N 个版本
│   │   └── --stream      # 流式输出
│   ├── settle            # 结算章节状态
│   ├── postcheck         # 运行确定性检查 gate
│   │   ├── --level       # quick / standard / deep
│   │   └── --whitelist   # 使用白名单过滤已确认警告
│   ├── audit             # 运行多维审计
│   ├── critique          # 6 维度 LLM 批评循环
│   ├── revise            # 执行修订（spot-fix 模式）
│   ├── approve           # 人工放行
│   ├── show              # 显示章节内容 + 元信息
│   ├── list              # 列出所有章节
│   ├── compare           # 比较多版本章节
│   ├── summarize         # 生成/更新章节摘要
│   └── rewrite           # 全章重写（blocker 级别时使用）
│
├── state
│   ├── show              # 显示当前 canonical state 摘要
│   ├── diff              # 两个版本之间的状态差异
│   ├── timeline          # 显示时间线
│   ├── hooks             # 显示未回收伏笔
│   ├── characters        # 显示角色当前状态一览
│   └── validate          # 验证状态一致性
│       └── --fix-suggest # 输出自动修复建议
│
├── snapshot
│   ├── create            # 创建快照
│   ├── list              # 列出所有快照
│   ├── diff              # 比较两个快照
│   ├── rollback          # 回滚到指定快照
│   └── delete            # 删除快照
│
├── import
│   ├── book              # 导入既有小说文本
│   │   └── --split       # 按正则拆分章节
│   ├── canon             # 导入母本（番外写作模式）
│   ├── bootstrap         # 从导入文本自动建立 world model
│   └── verify            # 验证导入后状态
│
├── detect
│   ├── run               # 对文本运行 AIGC 检测
│   ├── stats             # 检测历史统计
│   └── anti-ai           # 去 AI 味改写
│
├── style
│   ├── analyze           # 分析文本风格指纹
│   └── import            # 导入风格参考
│
├── genre
│   ├── list              # 列出可用题材模板
│   ├── show              # 显示题材详情
│   ├── create            # 创建自定义题材
│   └── copy              # 复制并修改题材模板
│
├── inspect
│   ├── rules             # 显示当前生效规则
│   ├── audit-report      # 显示最近审计报告
│   ├── postcheck-report  # 显示最近 postcheck 报告
│   ├── style-report      # 显示风格分析报告
│   ├── text-audit        # 运行离线文本审计
│   ├── pacing            # 节奏/弧线分析
│   └── reader-sim        # 读者模拟报告
│
├── analytics
│   ├── summary           # 审计通过率、高频问题、成本追踪
│   └── chapters          # 章节质量排名
│
├── prompt
│   ├── list              # 列出 prompt 模板
│   ├── show              # 查看模板内容
│   └── edit              # 编辑模板（打开编辑器）
│
├── rules
│   ├── list              # 列出规则
│   ├── add               # 添加规则
│   ├── update            # 更新规则
│   ├── disable           # 禁用规则
│   └── test              # 对文本测试规则
│
├── daemon
│   ├── start             # 启动守护进程
│   ├── stop              # 停止守护进程
│   └── status            # 守护进程状态
│
├── doctor                # 配置诊断 + API 连通性测试
│
├── stats                 # 写作统计（字数/会话/时间/成本）
│
├── agent
│   ├── chat              # 交互式 agent 会话（React/Tool Agent 模式）
│   ├── run               # 运行指定 agent 任务（非交互）
│   └── status            # 查看 agent 会话状态
│
├── radar
│   └── scan              # 市场趋势扫描
│
└── session
    ├── status            # 当前会话状态
    └── history           # 命令历史
```

---

## 附录 A：对已有结论的修正说明

| 修正项 | 原结论 | 修正后 | 原因 | 工程影响 |
|--------|--------|--------|------|----------|
| 技术栈 | 未明确 | Python 3.12+ | InkOS 是 TypeScript 但 novelwriter2 核心是 Python；NLP/检测/审计工具链 Python 更成熟；CLI-Anything 验证过 Python + Click 模式 | InkOS 核心逻辑需要 TS→Python 移植 |
| 存储方案 | 未明确 | 先 JSON 文件，后期可选 SQLite | 文件方案简单、可 diff、可 git 追踪；MVP 阶段避免数据库复杂度 | 需要在 Phase 0 确认 schema 兼容文件和 SQLite 两种方案 |
| 审计维度 | InkOS 33 维度 | Phase 3 先做 15-20 维度核心子集 | 33 维度调参工作量大，先用最有价值的子集验证 | Phase 5 再扩展到完整集 |
| CLI-Anything 的定位 | 可能被误解为"可以直接套用的框架" | 明确为"只借打包模式，不借业务逻辑" | CLI-Anything 的核心价值是"给 GUI 软件生成 CLI"，小说系统没有 GUI 后端可调 | 需要自建全部 Runtime 层 |
| NovelForge 灵感助手/Studio | v1 标记为 ❌ 不纳入（UI 功能） | 🔧 纳入：agent_session.py + schema.py 增强 | 后端有完整 React/Tool Agent 链路和 Schema 合成逻辑，不是纯 UI | 新增 llm/agent_session.py、schema.py 增强、CLI `novel agent` 命令组 |
| AI_Gen_Novel 段落级迭代 | v1 标记为 ❌ 不纳入（粒度不匹配） | 🔧 纳入：适配到场景级 iteration | plan→write→embellish→memory 循环对章内质量有直接价值 | drafter.py 内部新增 scene-level iteration |
| newtype-profile Agent 框架 | v1 标记为 ❌ 不纳入（采用固定流水线） | 🔧 纳入为可选编排层 | 模块化框架可叠加在固定流水线之上，两种模式共存 | 新增 orchestration/ 目录、Phase 6.5 |
| NovelGenerator API resilience | v1 标记为 ❌ 不纳入（工程细节） | 🔧 纳入：llm/resilience.py | 含错误分类、优先队列、动态限速，是 LLM 抽象层必要能力 | 新增 llm/resilience.py、Phase 3 交付物更新 |
| Skill 层硬编码边界 | v1 未明确 | Skill 只做纯编排，硬逻辑必须在 Runtime | 6 个 Skill 流程含条件判断，判断规则必须由 Runtime 返回结构化 JSON | Runtime CLI 输出必须包含 recommended_action/severity/expired 等字段 |
| 固定流水线 vs Agent 驱动 | v1 只有固定流水线 | 两者共存，固定流水线为默认 | 固定流水线可控可预测；Agent 驱动灵活但风险高 | 新增 Phase 6.5、`novel agent` 命令组 |
| CLI-Anything SOP 适配性 | v1 定位为"打包模式参考" | 细化为"三层借用架构"：① 复制工具文件 ② 创建 novel-dev-sop Skill 编码适配后的方法论 ③ novel-cli 最终产物 | HARNESS.md Phase 1 的 5 个核心假设在新建整合型项目中均不成立；但 Phase 2-7 方法论有直接复用价值 | Phase 0 前完成：复制工具文件 + 创建 novel-dev-sop Skill；不改造 CLI-Anything 本身 |
