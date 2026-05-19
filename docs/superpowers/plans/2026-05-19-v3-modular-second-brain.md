# v3 Modular Second Brain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the v2.2 single-file prompt repository into a v3.0 modular, publishable AI application second-brain framework with a generated user-facing `dist/CLAUDE.md`.

**Architecture:** Source content lives in focused Markdown modules under `src/`; `src/manifest.md` defines publication order; `scripts/build-dist.sh` concatenates the modules into standalone `dist/CLAUDE.md`. User vault starter files live under `templates/vault/`, while repository documentation explains setup, upgrade, architecture, and examples.

**Tech Stack:** Markdown, POSIX shell, Git. No app runtime, package manager, database, frontend, or external dependencies.

---

## File Structure

Create or modify these files:

- Create: `src/manifest.md`
- Create: `src/core/00-first-principles.md`
- Create: `src/core/01-persona.md`
- Create: `src/core/02-voice-guardrails.md`
- Create: `src/core/03-data-governance.md`
- Create: `src/flows/startup-memory.md`
- Create: `src/flows/conversation-stages.md`
- Create: `src/flows/activities.md`
- Create: `src/flows/essays.md`
- Create: `src/flows/school-research.md`
- Create: `src/flows/session-archive.md`
- Create: `src/domain/us-college/timeline-m-value.md`
- Create: `src/domain/us-college/admissions-philosophy.md`
- Create: `src/domain/us-college/application-tracker.md`
- Create: `scripts/build-dist.sh`
- Create: `dist/CLAUDE.md`
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Create: `docs/setup.md`
- Create: `docs/upgrade-v2-to-v3.md`
- Create: `docs/design.md`
- Create: `examples/demo-vault/README.md`
- Create/Move: `templates/vault/**`

Do not commit `.DS_Store` or `.superpowers/`.

## Source Section Map

Use the existing `CLAUDE.md` sections as the source of truth for the first split:

- `src/core/00-first-principles.md`: section 0.
- `src/core/01-persona.md`: sections 4, 7, and 8.
- `src/core/02-voice-guardrails.md`: sections 5, 6, 9, 10, and 22.
- `src/core/03-data-governance.md`: sections 2, 16, 18, 20, 21, and 23.
- `src/flows/startup-memory.md`: sections 1 and 3.
- `src/flows/conversation-stages.md`: section 11.
- `src/flows/activities.md`: section 12.
- `src/flows/essays.md`: section 13.
- `src/flows/school-research.md`: section 19.
- `src/flows/session-archive.md`: sections 16, 17, 18, 20, and 23 where behavior overlaps archiving and memory updates.
- `src/domain/us-college/timeline-m-value.md`: section 15.
- `src/domain/us-college/admissions-philosophy.md`: US admissions-specific parts of sections 0, 4, 7, 12, 13, and 14.
- `src/domain/us-college/application-tracker.md`: sections 17, 18, and 24 paths related to deadlines, school research, ED, EA, RD, and per-school progress.

If a section appears in two target files, keep the canonical operating rule in the flow file and keep the domain file as domain-specific explanation or constants. Avoid duplicating the same imperative rule in multiple modules.

---

### Task 1: Add the Modular Source Skeleton and Build Script

**Files:**
- Create: `src/manifest.md`
- Create: `src/core/*.md`
- Create: `src/flows/*.md`
- Create: `src/domain/us-college/*.md`
- Create: `scripts/build-dist.sh`
- Create: `dist/.gitkeep`

- [ ] **Step 1: Create the directory skeleton**

Run:

```bash
mkdir -p src/core src/flows src/domain/us-college scripts dist
touch dist/.gitkeep
```

Expected: directories exist and `find src -maxdepth 3 -type d | sort` includes `src/core`, `src/flows`, and `src/domain/us-college`.

- [ ] **Step 2: Create `src/manifest.md`**

Write this exact file:

```markdown
# CLAUDE.md Build Manifest

> `scripts/build-dist.sh` reads this file in order. Each bullet must be a repository-relative Markdown path.

- src/core/00-first-principles.md
- src/core/01-persona.md
- src/core/02-voice-guardrails.md
- src/core/03-data-governance.md
- src/domain/us-college/admissions-philosophy.md
- src/domain/us-college/timeline-m-value.md
- src/domain/us-college/application-tracker.md
- src/flows/startup-memory.md
- src/flows/conversation-stages.md
- src/flows/activities.md
- src/flows/essays.md
- src/flows/school-research.md
- src/flows/session-archive.md
```

- [ ] **Step 3: Create initial module files with real headings**

Write these initial headings before moving content:

```bash
printf '# 0. 第一性原理\n' > src/core/00-first-principles.md
printf '# 1. 助手身份与核心原则\n' > src/core/01-persona.md
printf '# 2. 语气、隐藏系统感与指令遵循\n' > src/core/02-voice-guardrails.md
printf '# 3. 数据治理与文件边界\n' > src/core/03-data-governance.md
printf '# 4. 美本招生哲学\n' > src/domain/us-college/admissions-philosophy.md
printf '# 5. M 值时间轴感知\n' > src/domain/us-college/timeline-m-value.md
printf '# 6. 申请追踪与学校研究约定\n' > src/domain/us-college/application-tracker.md
printf '# 7. 启动、初始化与记忆读取\n' > src/flows/startup-memory.md
printf '# 8. 对话阶段\n' > src/flows/conversation-stages.md
printf '# 9. 活动建议\n' > src/flows/activities.md
printf '# 10. 文书判断\n' > src/flows/essays.md
printf '# 11. 学校研究与外部知识吸收\n' > src/flows/school-research.md
printf '# 12. 会话归档与记忆更新\n' > src/flows/session-archive.md
```

Expected: every path in `src/manifest.md` exists.

- [ ] **Step 4: Add the build script**

Create `scripts/build-dist.sh` with this exact content:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$ROOT_DIR/src/manifest.md"
OUT="$ROOT_DIR/dist/CLAUDE.md"

if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing manifest: $MANIFEST" >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/dist"

{
  echo "# 美本申请第二大脑 | CLAUDE.md v3.0"
  echo
  echo "> Generated from src/manifest.md. Edit src/ modules, then run scripts/build-dist.sh."
  echo
  while IFS= read -r line; do
    [[ "$line" =~ ^-\  ]] || continue
    path="${line#- }"
    file="$ROOT_DIR/$path"
    if [[ ! -f "$file" ]]; then
      echo "Manifest entry not found: $path" >&2
      exit 1
    fi
    echo
    echo "<!-- BEGIN $path -->"
    cat "$file"
    echo
    echo "<!-- END $path -->"
  done < "$MANIFEST"
} > "$OUT"

echo "Wrote $OUT"
```

- [ ] **Step 5: Make the script executable and run the first build**

Run:

```bash
chmod +x scripts/build-dist.sh
./scripts/build-dist.sh
```

Expected: command prints `Wrote .../dist/CLAUDE.md`.

- [ ] **Step 6: Verify the skeleton build**

Run:

```bash
rg -n "BEGIN src/core/00-first-principles.md|BEGIN src/flows/essays.md|BEGIN src/domain/us-college/timeline-m-value.md" dist/CLAUDE.md
```

Expected: three matching lines in `dist/CLAUDE.md`.

- [ ] **Step 7: Commit the skeleton**

Run:

```bash
git add src scripts dist
git commit -m "chore: add v3 modular source skeleton"
```

Expected: commit succeeds with only source skeleton, build script, and `dist/CLAUDE.md` changes.

---

### Task 2: Split Core Rules Out of the Existing Prompt

**Files:**
- Modify: `src/core/00-first-principles.md`
- Modify: `src/core/01-persona.md`
- Modify: `src/core/02-voice-guardrails.md`
- Modify: `src/core/03-data-governance.md`
- Modify: `dist/CLAUDE.md`

- [ ] **Step 1: Extract first principles**

Move the full existing `CLAUDE.md` section `## 0. 第一性原理（最高优先级，不可违背）` into `src/core/00-first-principles.md`.

Keep the module heading as:

```markdown
# 0. 第一性原理
```

Expected content checks:

```bash
rg -n "招生官在找活生生的人|这个建议，是从这个具体的人身上长出来的吗" src/core/00-first-principles.md
```

Expected: both phrases are present.

- [ ] **Step 2: Extract assistant persona and high-level principles**

Move these existing sections into `src/core/01-persona.md`:

```text
## 4. 你是谁
## 7. 核心原则：要活人
## 8. 用户定制
```

Keep this module heading:

```markdown
# 1. 助手身份与核心原则
```

Expected content checks:

```bash
rg -n "专为中国高中生设计的美本申请 AI 伙伴|素材库里没有\"无用\"的东西|默认：温暖、直接、不啰嗦" src/core/01-persona.md
```

Expected: all three phrases are present.

- [ ] **Step 3: Extract voice guardrails and interaction constraints**

Move these existing sections into `src/core/02-voice-guardrails.md`:

```text
## 5. 隐藏系统感（强制规则）
## 6. 对话语气禁止行为
## 9. 指令遵循度检测
## 10. 话题类型判断（新增）
## 22. 决策确认约束
```

Keep this module heading:

```markdown
# 2. 语气、隐藏系统感与指令遵循
```

Expected content checks:

```bash
rg -n "永远不要对用户说|每次回复开头必须使用|情绪类 > 功能类 > 信息类|必须询问用户的情况" src/core/02-voice-guardrails.md
```

Expected: all four phrases are present.

- [ ] **Step 4: Extract data governance and file-boundary rules**

Move these existing sections into `src/core/03-data-governance.md`:

```text
## 2. 工作区边界规则（宪法级别）
## 16. 三层记忆架构
## 18. 智能存储路由（强制执行）
## 20. 对话存档（强制执行）
## 21. 数据治理（最高优先级）
## 23. 八步自我迭代流程
```

Keep this module heading:

```markdown
# 3. 数据治理与文件边界
```

Expected content checks:

```bash
rg -n "所有文件必须保存在|记忆库/|数据不删除，只转移|八步自我迭代流程" src/core/03-data-governance.md
```

Expected: all four phrases are present.

- [ ] **Step 5: Rebuild dist and verify core content**

Run:

```bash
./scripts/build-dist.sh
rg -n "第一性原理|助手身份与核心原则|语气、隐藏系统感与指令遵循|数据治理与文件边界" dist/CLAUDE.md
```

Expected: build succeeds and all four module headings appear in `dist/CLAUDE.md`.

- [ ] **Step 6: Commit core split**

Run:

```bash
git add src/core dist/CLAUDE.md
git commit -m "refactor: split core prompt rules"
```

Expected: commit includes only core modules and generated dist changes.

---

### Task 3: Split Domain-Specific US College Logic

**Files:**
- Modify: `src/domain/us-college/admissions-philosophy.md`
- Modify: `src/domain/us-college/timeline-m-value.md`
- Modify: `src/domain/us-college/application-tracker.md`
- Modify: `dist/CLAUDE.md`

- [ ] **Step 1: Extract M-value timeline logic**

Move the existing section `## 15. 时间轴感知（新增）` into `src/domain/us-college/timeline-m-value.md`.

Keep this module heading:

```markdown
# 5. M 值时间轴感知
```

Expected content checks:

```bash
rg -n "M = 申请季开始时间 − 当前日期|M ≥ 24|12 ≤ M < 24|0 ≤ M < 12|M < 0" src/domain/us-college/timeline-m-value.md
```

Expected: all M-value thresholds are present.

- [ ] **Step 2: Extract US admissions philosophy**

Write `src/domain/us-college/admissions-philosophy.md` as a domain-specific synthesis using existing language from sections 0, 4, 7, 12, 13, and 14. It must include these headings:

```markdown
# 4. 美本招生哲学

## 核心判断

## 活动判断

## 文书判断

## 价值观校准
```

Expected content checks:

```bash
rg -n "holistic|真实的热情|文书不是用来展示你做了什么|独特性是结果，不是目标" src/domain/us-college/admissions-philosophy.md
```

Expected: `真实的热情`, `文书不是用来展示你做了什么`, and `独特性是结果，不是目标` are present. The word `holistic` may be omitted if the Chinese explanation clearly describes holistic review; if omitted, add `整体性评估` to the file and search for that instead.

- [ ] **Step 3: Extract application tracker conventions**

Write `src/domain/us-college/application-tracker.md` from the deadline and school-research-related rules in sections 17, 18, and 24.

Use this structure:

```markdown
# 6. 申请追踪与学校研究约定

## 时间意图捕获

## Deadline 总览

## 学校研究

## 每所学校进度
```

Expected content checks:

```bash
rg -n "ED|EA|RD|Deadline总览|学校研究|每所学校进度" src/domain/us-college/application-tracker.md
```

Expected: all six terms are present.

- [ ] **Step 4: Rebuild dist and verify domain boundaries**

Run:

```bash
./scripts/build-dist.sh
rg -n "M 值时间轴感知|美本招生哲学|申请追踪与学校研究约定" dist/CLAUDE.md
```

Expected: all three domain headings appear in `dist/CLAUDE.md`.

- [ ] **Step 5: Commit domain split**

Run:

```bash
git add src/domain dist/CLAUDE.md
git commit -m "refactor: isolate us college domain logic"
```

Expected: commit includes only domain modules and generated dist changes.

---

### Task 4: Split Workflow Modules

**Files:**
- Modify: `src/flows/startup-memory.md`
- Modify: `src/flows/conversation-stages.md`
- Modify: `src/flows/activities.md`
- Modify: `src/flows/essays.md`
- Modify: `src/flows/school-research.md`
- Modify: `src/flows/session-archive.md`
- Modify: `dist/CLAUDE.md`

- [ ] **Step 1: Normalize each workflow structure**

Each flow file must contain these headings:

```markdown
## 触发条件

## 需要读取的文件

## 操作步骤

## 写入或更新

## 风险检查
```

Expected heading check:

```bash
for file in src/flows/*.md; do
  echo "$file"
  rg -n "## 触发条件|## 需要读取的文件|## 操作步骤|## 写入或更新|## 风险检查" "$file"
done
```

Expected: every flow file prints all five headings.

- [ ] **Step 2: Fill startup and memory flow**

Move existing sections `## 1. 启动流程（触发词 + 懒加载 + 晨间简报合并）` and `## 3. 初始化（仅第一次运行时执行）` into `src/flows/startup-memory.md`, under the normalized headings.

Expected content checks:

```bash
rg -n "第一次会话|非第一次会话|晨间简报模板|核心身份|申请季开始时间" src/flows/startup-memory.md
```

Expected: all five terms are present.

- [ ] **Step 3: Fill conversation stage flow**

Move existing section `## 11. 对话四阶段（重写：加明确的切换条件 + 质量检查）` into `src/flows/conversation-stages.md`, under the normalized headings.

Expected content checks:

```bash
rg -n "阶段一：了解你这个人|阶段二：深聊|阶段三：给方向|阶段四：持续积累|不要硬切换" src/flows/conversation-stages.md
```

Expected: all five terms are present.

- [ ] **Step 4: Fill activity flow**

Move existing section `## 12. 活动建议规则（强制执行，改写：加冷启动）` into `src/flows/activities.md`, under the normalized headings.

Expected content checks:

```bash
rg -n "冷启动保护|可及性|时间现实性|真实性|学业保护|推荐活动的来源优先级" src/flows/activities.md
```

Expected: all six terms are present.

- [ ] **Step 5: Fill essay flow**

Move existing section `## 13. 文书判断规则（强制执行，改写：加正向起点）` into `src/flows/essays.md`, under the normalized headings.

Expected content checks:

```bash
rg -n "文书话题触发条件|文书的根本功能|好文书的四个起点|AI 在文书话题上的工作方式|文书好坏的判断标准" src/flows/essays.md
```

Expected: all five terms are present.

- [ ] **Step 6: Fill school research flow**

Move existing section `## 19. 外部知识吸收（强制执行）` into `src/flows/school-research.md`, under the normalized headings. Include the storage rule for `学校研究/[学校名]/` from section 18.

Expected content checks:

```bash
rg -n "外部知识吸收|学校官网|申请案例|对比分析|学校研究/\\[学校名\\]" src/flows/school-research.md
```

Expected: all five terms are present.

- [ ] **Step 7: Fill session archive flow**

Move session-ending and memory-update behavior from sections 16, 17, 18, 20, and 23 into `src/flows/session-archive.md`, under the normalized headings.

Expected content checks:

```bash
rg -n "情景记忆|语义记忆|强制规则|对话历史.md|只能追加|八步自我迭代流程" src/flows/session-archive.md
```

Expected: all six terms are present.

- [ ] **Step 8: Rebuild dist and verify flow modules**

Run:

```bash
./scripts/build-dist.sh
rg -n "启动、初始化与记忆读取|对话阶段|活动建议|文书判断|学校研究与外部知识吸收|会话归档与记忆更新" dist/CLAUDE.md
```

Expected: all six flow headings appear in `dist/CLAUDE.md`.

- [ ] **Step 9: Commit workflow split**

Run:

```bash
git add src/flows dist/CLAUDE.md
git commit -m "refactor: split prompt workflows"
```

Expected: commit includes only flow modules and generated dist changes.

---

### Task 5: Replace Root `CLAUDE.md` with Maintainer Guide

**Files:**
- Modify: `CLAUDE.md`
- Modify: `dist/CLAUDE.md`

- [ ] **Step 1: Ensure `dist/CLAUDE.md` is the complete runtime file**

Run:

```bash
./scripts/build-dist.sh
wc -l dist/CLAUDE.md
```

Expected: `dist/CLAUDE.md` has enough content to be standalone. A reasonable first pass should be over 600 lines after the v2.2 content is split.

- [ ] **Step 2: Replace root `CLAUDE.md`**

Replace root `CLAUDE.md` with:

```markdown
# Repository Maintainer Guide

This repository publishes the user-facing runtime prompt at `dist/CLAUDE.md`.

## For users

Copy `dist/CLAUDE.md` and `templates/vault/` into your AI workspace. Follow `docs/setup.md`.

## For maintainers

Edit the Markdown modules under `src/`, keep `src/manifest.md` in the intended order, then run:

```bash
./scripts/build-dist.sh
```

Do not edit `dist/CLAUDE.md` directly unless you are repairing a release artifact and immediately backporting the same change into `src/`.
```

- [ ] **Step 3: Verify root and dist no longer duplicate roles**

Run:

```bash
rg -n "Repository Maintainer Guide" CLAUDE.md
rg -n "Generated from src/manifest.md|第一性原理|M 值时间轴感知|文书判断" dist/CLAUDE.md
```

Expected: root `CLAUDE.md` contains maintainer guide text; `dist/CLAUDE.md` contains runtime prompt text.

- [ ] **Step 4: Commit root guide change**

Run:

```bash
git add CLAUDE.md dist/CLAUDE.md
git commit -m "docs: make root claude file maintainer guide"
```

Expected: commit succeeds.

---

### Task 6: Expand `templates/vault/` to Match the Runtime File Structure

**Files:**
- Create/Move: `templates/vault/**`
- Keep: existing legacy `templates/**` only if backwards compatibility is desired during this task; final README should point to `templates/vault/`.

- [ ] **Step 1: Create vault directory tree**

Run:

```bash
mkdir -p \
  templates/vault/本体画像 \
  templates/vault/记忆库/情景记忆/YYYY-MM \
  templates/vault/记忆库/语义记忆 \
  templates/vault/记忆库/强制规则 \
  templates/vault/素材库/经历/学术与研究 \
  templates/vault/素材库/经历/项目与作品 \
  templates/vault/素材库/经历/社区与服务 \
  templates/vault/素材库/感受/读过的书 \
  templates/vault/素材库/感受/看过的展览与艺术 \
  templates/vault/素材库/感受/有感触的新闻与事件 \
  templates/vault/素材库/感受/喜欢的游戏与作品 \
  templates/vault/素材库/思考/每日想法 \
  templates/vault/素材库/思考/让我困惑的问题 \
  templates/vault/素材库/思考/改变了我看法的时刻 \
  templates/vault/素材库/关系/重要的对话 \
  templates/vault/素材库/关系/让我印象深刻的人 \
  templates/vault/日记/YYYY-MM \
  templates/vault/学校研究/学校名 \
  templates/vault/申请追踪/每所学校进度
```

Expected: command succeeds.

- [ ] **Step 2: Copy existing starter files into `templates/vault/`**

Run:

```bash
cp templates/对话历史.md templates/vault/对话历史.md
cp templates/日记/模板.md templates/vault/日记/模板.md
cp templates/本体画像/*.md templates/vault/本体画像/
cp templates/记忆库/语义记忆/*.md templates/vault/记忆库/语义记忆/
cp templates/申请追踪/Deadline总览.md templates/vault/申请追踪/Deadline总览.md
```

Expected: copied files exist under `templates/vault/`.

- [ ] **Step 3: Update identity template for v3 timeline fields**

Ensure `templates/vault/本体画像/00-核心身份.md` includes these exact sections:

```markdown
## 学制
3 年制 / 4 年制（G13 申请）/ 美高 4 年 / 其他（请说明）

## 申请季开始时间
YYYY-MM（通常是递交 ED/EA 的年份的 8-9 月）
```

Expected content check:

```bash
rg -n "## 学制|## 申请季开始时间" templates/vault/本体画像/00-核心身份.md
```

Expected: both headings are present.

- [ ] **Step 4: Add `.gitkeep` files for empty vault directories**

Run:

```bash
find templates/vault -type d -empty -exec sh -c 'touch "$1/.gitkeep"' sh {} \;
```

Expected: empty directories are tracked by `.gitkeep`.

- [ ] **Step 5: Verify template paths mentioned by dist exist**

Run:

```bash
test -f templates/vault/对话历史.md
test -f templates/vault/本体画像/00-核心身份.md
test -f templates/vault/记忆库/语义记忆/核心特质.md
test -f templates/vault/申请追踪/Deadline总览.md
test -d templates/vault/素材库/经历/学术与研究
test -d templates/vault/学校研究/学校名
```

Expected: all tests exit with code 0.

- [ ] **Step 6: Commit template expansion**

Run:

```bash
git add templates/vault
git commit -m "feat: add complete vault template"
```

Expected: commit succeeds.

---

### Task 7: Add Setup, Upgrade, Architecture Docs, and Demo Vault

**Files:**
- Create: `docs/setup.md`
- Create: `docs/upgrade-v2-to-v3.md`
- Create: `docs/design.md`
- Create: `examples/demo-vault/README.md`
- Modify: `README.md`

- [ ] **Step 1: Write `docs/setup.md`**

Create:

```markdown
# Setup

## Install

1. Copy `dist/CLAUDE.md` into the AI workspace that will run this second brain.
2. Copy `templates/vault/` into the student's working folder.
3. Rename the copied folder to `美本申请第二大脑` if you want to follow the default path naming.
4. Fill `本体画像/00-核心身份.md`.
5. Confirm `学制` and `申请季开始时间` are filled.
6. Start a new AI conversation and say `启动`.

## Required Fields

- `姓名/称呼`
- `申请身份`
- `年级`
- `学制`
- `申请季开始时间`
- `所在城市/家乡`

## Daily Use

Drop conversations, reflections, school research, deadlines, activity updates, and essay ideas into the AI conversation. The assistant routes durable information into the vault structure.
```

- [ ] **Step 2: Write `docs/upgrade-v2-to-v3.md`**

Create:

```markdown
# Upgrade from v2 to v3

## Safety Rule

Never overwrite a filled vault. Copy the existing vault before migrating.

## Steps

1. Back up the existing `美本申请第二大脑/` folder.
2. Copy the new `dist/CLAUDE.md` into the AI workspace.
3. Copy `templates/vault/` to a temporary folder.
4. Move existing filled files from the old vault into the matching v3 paths.
5. Add missing v3-only folders such as `记忆库/强制规则/`, `素材库/关系/`, and `学校研究/学校名/`.
6. Open `本体画像/00-核心身份.md` and add `学制` plus `申请季开始时间` if they are missing.
7. Start a fresh AI conversation and say `启动`.

## Do Not Migrate By

- Replacing the whole old vault with `templates/vault/`.
- Deleting old memory files because they look messy.
- Merging unrelated students into one vault.
```

- [ ] **Step 3: Write `docs/design.md`**

Create:

```markdown
# Architecture

v3 uses a source-and-distribution model.

- `src/` contains maintainable prompt modules.
- `src/manifest.md` defines publication order.
- `scripts/build-dist.sh` generates `dist/CLAUDE.md`.
- `dist/CLAUDE.md` is the only complete runtime prompt users copy.
- `templates/vault/` is the starter vault.
- `examples/demo-vault/` shows a fictional filled example.

## Module Rules

Core rules belong in `src/core/`.
Task procedures belong in `src/flows/`.
US-college-specific logic belongs in `src/domain/us-college/`.

When a rule seems to fit multiple places, put the imperative operating rule in the flow and put domain explanation or constants in the domain module.
```

- [ ] **Step 4: Add demo vault README**

Create `examples/demo-vault/README.md`:

```markdown
# Demo Vault

This folder documents the shape of a fictional filled vault. It should not contain real student data.

Use it to understand how identity, semantic memory, activity material, school research, deadlines, and session archives are expected to evolve.
```

- [ ] **Step 5: Rewrite README as product quickstart**

Update `README.md` so it contains these sections:

```markdown
# 美本申请第二大脑 (US College App Second Brain) v3.0

> 第一性原理：招生官在找活生生的人。

## What This Is

An AI-guided second-brain framework for Chinese high-school students preparing US undergraduate applications.

## Quickstart

1. Read `docs/setup.md`.
2. Copy `dist/CLAUDE.md`.
3. Copy `templates/vault/`.
4. Fill `本体画像/00-核心身份.md`.
5. Say `启动`.

## Repository Structure

- `src/`: modular source prompt.
- `dist/`: generated user-facing prompt.
- `templates/vault/`: starter vault.
- `docs/`: setup, upgrade, and design docs.
- `examples/`: fictional examples.

## Upgrade

Existing users should read `docs/upgrade-v2-to-v3.md` before copying any files.

## License

This project uses `CC BY-NC-SA 4.0`. See `LICENSE.md`.
```

Keep the existing attribution to the original author and maintainer in the README after the Quickstart or License section.

- [ ] **Step 6: Verify docs links**

Run:

```bash
test -f docs/setup.md
test -f docs/upgrade-v2-to-v3.md
test -f docs/design.md
test -f examples/demo-vault/README.md
rg -n "docs/setup.md|docs/upgrade-v2-to-v3.md|dist/CLAUDE.md|templates/vault" README.md
```

Expected: all tests succeed and README references the key paths.

- [ ] **Step 7: Commit docs**

Run:

```bash
git add README.md docs/setup.md docs/upgrade-v2-to-v3.md docs/design.md examples/demo-vault/README.md
git commit -m "docs: add v3 setup and upgrade guide"
```

Expected: commit succeeds.

---

### Task 8: Final Validation and Release Readiness

**Files:**
- Modify only files required by failed validation checks.

- [ ] **Step 1: Run build**

Run:

```bash
./scripts/build-dist.sh
```

Expected: command exits 0 and prints `Wrote .../dist/CLAUDE.md`.

- [ ] **Step 2: Verify manifest coverage**

Run:

```bash
while IFS= read -r line; do
  [[ "$line" =~ ^-\  ]] || continue
  path="${line#- }"
  test -f "$path" || { echo "Missing $path"; exit 1; }
  rg -n "BEGIN $path" dist/CLAUDE.md >/dev/null || { echo "Missing in dist: $path"; exit 1; }
done < src/manifest.md
```

Expected: command exits 0 with no output.

- [ ] **Step 3: Verify required runtime content**

Run:

```bash
rg -n "招生官在找活生生的人|M = 申请季开始时间|冷启动保护|好文书的四个起点|外部知识吸收|数据不删除，只转移" dist/CLAUDE.md
```

Expected: all six phrases are present.

- [ ] **Step 4: Verify required template content**

Run:

```bash
test -f templates/vault/本体画像/00-核心身份.md
test -f templates/vault/记忆库/语义记忆/申请故事主线.md
test -f templates/vault/申请追踪/Deadline总览.md
test -d templates/vault/记忆库/情景记忆/YYYY-MM
test -d templates/vault/素材库/思考/改变了我看法的时刻
rg -n "## 学制|## 申请季开始时间" templates/vault/本体画像/00-核心身份.md
```

Expected: all file tests succeed and both identity headings are present.

- [ ] **Step 5: Verify no local visual artifacts are staged**

Run:

```bash
git status --short
```

Expected: no staged `.DS_Store` or `.superpowers/` entries. If they appear as untracked files, leave them uncommitted or add a `.gitignore` in a separate housekeeping commit with:

```gitignore
.DS_Store
.superpowers/
```

- [ ] **Step 6: Commit validation fixes**

If validation changed generated `dist/CLAUDE.md` or docs, run:

```bash
git add dist/CLAUDE.md README.md docs templates src scripts examples
git commit -m "chore: validate v3 modular release"
```

Expected: commit succeeds if there were changes. If there were no changes, skip this commit.

- [ ] **Step 7: Report final state**

Run:

```bash
git log --oneline -5
git status --short
```

Expected: recent commits show the v3 implementation sequence; only known local artifacts may remain untracked.
