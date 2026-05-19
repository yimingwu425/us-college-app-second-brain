# 美本申请第二大脑 v3.0 模块化设计

## 背景

当前 v2.2 仓库的核心价值集中在 `CLAUDE.md`：它定义了第一性原理、人格、对话阶段、活动建议、文书判断、M 值时间轴、记忆系统和文件结构。这个设计已经形成了清晰的产品判断，但实现上仍是一个 1000+ 行的单文件提示词包。

主要问题：

- 规则、流程、模板、算法、存储约定和版本记录混在同一个文件里。
- `templates/` 与 `CLAUDE.md` 声明的完整工作区结构不一致。
- 用户安装方式依赖手动复制，缺少 setup、upgrade、demo 和发布说明。
- 后续扩展到英本、研究生、转学等场景时，通用第二大脑逻辑和美本领域逻辑会互相缠绕。

v3.0 的目标不是把项目做成 App，也不是引入复杂 CLI，而是把它升级为可维护、可发布、可复用的 AI 申请第二大脑框架。

## 目标

v3.0 采用“模块化源码 + 单文件发布”的双轨结构：

- 维护者编辑 `src/` 下的模块化源码。
- 普通用户复制 `dist/CLAUDE.md` 和 `templates/vault/` 即可使用。
- 当前默认领域仍是美本申请，但核心框架不硬编码美本。
- 文档补齐安装、升级、设计和示例工作区，降低别人复用门槛。

## 非目标

- 不做完整 App。
- 不做复杂命令行工具。
- 不引入数据库、前端界面或云同步。
- 不把美本申请体验稀释成泛泛的“人生规划”助手。
- 不在 v3.0 阶段实现英本、研究生、转学等新领域，只预留结构边界。

## 推荐方案

采用“可发布框架 v3.0”：

1. 将 `CLAUDE.md` 拆分到 `src/core/`、`src/flows/`、`src/domain/us-college/`。
2. 用 `src/manifest.md` 定义拼装顺序。
3. 生成或维护 `dist/CLAUDE.md` 作为用户可复制的完整单文件。
4. 将模板扩展为 `templates/vault/`，保证它和系统声明的文件结构一致。
5. 增加 `docs/setup.md`、`docs/upgrade-v2-to-v3.md`、`docs/design.md` 和 `examples/demo-vault/`。

这个方案在可维护性、公开复用和实现成本之间最平衡。

## 目录结构

```text
.
├── README.md
├── CLAUDE.md
├── dist/
│   └── CLAUDE.md
├── src/
│   ├── manifest.md
│   ├── core/
│   │   ├── 00-first-principles.md
│   │   ├── 01-persona.md
│   │   ├── 02-voice-guardrails.md
│   │   └── 03-data-governance.md
│   ├── flows/
│   │   ├── startup-memory.md
│   │   ├── conversation-stages.md
│   │   ├── activities.md
│   │   ├── essays.md
│   │   ├── school-research.md
│   │   └── session-archive.md
│   └── domain/
│       └── us-college/
│           ├── timeline-m-value.md
│           ├── admissions-philosophy.md
│           └── application-tracker.md
├── templates/
│   └── vault/
│       ├── 本体画像/
│       ├── 记忆库/
│       ├── 素材库/
│       ├── 日记/
│       ├── 学校研究/
│       └── 申请追踪/
├── docs/
│   ├── setup.md
│   ├── upgrade-v2-to-v3.md
│   └── design.md
└── examples/
    └── demo-vault/
```

`CLAUDE.md` at the repository root should become a short maintainer-facing guide for working on this repository. It should point users to `dist/CLAUDE.md` for installation. The user-facing complete runtime file belongs only in `dist/CLAUDE.md`, so there is a single source for copying into a student's workspace.

## Module Boundaries

### `src/core/`

Contains rules that apply across domains:

- First principle: admissions readers are looking for a living person.
- Assistant identity and relationship to the student.
- Voice guardrails and hidden-system rules.
- Topic type detection.
- Decision confirmation rules.
- Data governance: append-only history, no deletion except explicit user request or exact duplication.

These files should not contain school-specific deadlines, M-value thresholds, or US-college-only admissions assumptions unless they are phrased as general principles.

### `src/flows/`

Contains task workflows. Each flow uses the same internal shape:

1. Trigger conditions.
2. Files to read.
3. Steps to execute.
4. Files to write or update.
5. Risk checks.

Initial flows:

- `startup-memory.md`: first run, returning user startup, lazy loading, morning brief.
- `conversation-stages.md`: four-stage relationship flow and transition criteria.
- `activities.md`: activity advice, cold-start protection, authenticity checks.
- `essays.md`: essay topic discovery, danger patterns, positive starting points.
- `school-research.md`: external school information absorption and user-fit comparison.
- `session-archive.md`: conversation history and semantic memory updates.

### `src/domain/us-college/`

Contains US-college-specific logic:

- M-value timeline and stage weighting.
- Admissions philosophy specific to US holistic review.
- Application tracker conventions such as ED, EA, RD, and school-specific progress.

Future domains can add sibling directories such as `domain/uk-undergrad/` without changing `core/`.

### `templates/vault/`

Represents the actual working vault users copy or initialize. It must match the file structure described by `dist/CLAUDE.md`.

Required coverage:

- `本体画像/`
- `记忆库/情景记忆/`
- `记忆库/语义记忆/`
- `记忆库/强制规则/`
- `素材库/经历/`
- `素材库/感受/`
- `素材库/思考/`
- `素材库/关系/`
- `日记/`
- `学校研究/`
- `申请追踪/`

## Runtime Behavior

The v3.0 behavior should preserve the existing user experience:

```text
用户输入
  -> 识别话题类型
  -> 读取必要文件
  -> 进入对应 flow
  -> 生成回复
  -> 更新记忆/追踪/素材
  -> 追加会话记录
```

The assistant should continue to feel like a person, not a visible state machine. Internal labels such as flow names, stages, templates, and file-routing logic must not be exposed to the student during normal conversation.

## Distribution

The published user path is:

1. Copy `dist/CLAUDE.md` into the target AI workspace.
2. Copy `templates/vault/` into the user's second-brain folder.
3. Fill `本体画像/00-核心身份.md`, especially `学制` and `申请季开始时间`.
4. Say “启动”.

The maintainer path is:

1. Edit files in `src/`.
2. Keep `src/manifest.md` in the intended order.
3. Rebuild or manually update `dist/CLAUDE.md`.
4. Verify `dist/CLAUDE.md` includes all source sections in order.
5. Verify `templates/vault/` matches documented paths.

The first v3 implementation may use a simple documented manual build process. A scripted build can be added later if manual updates become error-prone.

## Documentation

Add:

- `docs/setup.md`: how a new user installs and starts.
- `docs/upgrade-v2-to-v3.md`: how an existing v2 user migrates files without losing data.
- `docs/design.md`: architecture overview for contributors.
- `examples/demo-vault/`: small fictional vault showing expected file shapes and memory evolution.

README should become a product landing and quickstart page, with links to setup, upgrade, license, and examples.

## Validation

Before v3.0 is considered complete:

- `dist/CLAUDE.md` can be read standalone and does not depend on hidden source files.
- Every path mentioned in `dist/CLAUDE.md` exists in `templates/vault/` or is explicitly described as created at runtime.
- `templates/vault/本体画像/00-核心身份.md` includes both `学制` and `申请季开始时间`.
- The M-value logic appears only in the US-college domain module and the generated dist file.
- Essay, activity, school-research, startup, memory, and archive behaviors each have a dedicated flow file.
- README explains the difference between `src/`, `dist/`, `templates/`, `docs/`, and `examples/`.
- The upgrade guide tells users never to overwrite their filled vault without backing it up.

## Open Decisions

The current design intentionally leaves one implementation choice for the next planning step:

- Whether `dist/CLAUDE.md` is assembled by a tiny script immediately in v3.0 or maintained manually for the first pass.

The recommended implementation plan should start with manual-safe modularization, then add a build script only if the split creates unacceptable duplication.
