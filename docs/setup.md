# 安装与使用

这份文档面向第一次使用项目的学生。完整流程是：

```text
克隆 GitHub 仓库
  -> 安装 brain 工具
  -> 创建独立的学生 vault
  -> 复制学生端 AGENTS.md
  -> 在 vault 目录打开 ZCode/Codex
  -> 用自然语言工作
```

## 1. 仓库和学生 vault 的区别

项目有两个目录，职责完全不同：

```text
us-college-app-second-brain/   GitHub 仓库
  提供 brain 工具、AGENTS.md、模板、测试和文档

~/college-vault/                学生工作区
  保存个人资料、申请任务、素材、文书、知识库和会话记录
```

学生的个人资料应该只放在 vault，不要放在项目仓库。以后启动 ZCode/Codex 时打开 vault 根目录。

## 2. 安装工具

### macOS / Linux

先确认 Python：

```bash
python3 --version
```

需要 Python 3.11 或更高版本。然后：

```bash
git clone https://github.com/yimingwu425/us-college-app-second-brain.git
cd us-college-app-second-brain
python3 -m pip install -e .
brain --help
```

如果终端提示 `brain: command not found`，通常是 Python 的用户脚本目录不在 PATH 中。此时可以使用：

```bash
python3 -m college_brain.cli --help
```

或者把 pip 显示的用户脚本目录加入 PATH 后重新打开终端。

### 建议：使用虚拟环境

如果不希望修改系统 Python：

```bash
cd us-college-app-second-brain
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
brain --help
```

以后使用前先进入仓库并激活环境：

```bash
cd /path/to/us-college-app-second-brain
source .venv/bin/activate
```

Windows PowerShell 的激活命令是：

```powershell
.venv\Scripts\Activate.ps1
```

## 3. 创建学生 vault

先决定：

- 你的本地时区，例如 `Asia/Shanghai`、`America/New_York`。
- 申请季开始月份，例如 2027 年秋季申请写 `2027-08`。

运行：

```bash
brain init ~/college-vault \
  --timezone Asia/Shanghai \
  --cycle 2027-08
```

`brain init` 只允许目标目录为空，避免覆盖已有资料。如果目录已经存在且里面有文件，请换一个新目录。

它会创建：

```text
~/college-vault/
  vault.yaml
  学生档案/
  用户画像.md
  素材库/
  学校研究/
  申请追踪/
  申请材料/
  状态/
  会话/
  knowledge/
  .brain/
```

检查初始化结果：

```bash
brain validate --path ~/college-vault
brain doctor --path ~/college-vault
```

两个命令都不报 error 后再进入下一步。

## 4. 安装学生端运行规则

ZCode/Codex 使用 `AGENTS.md`：

```bash
cp dist/AGENTS.md ~/college-vault/AGENTS.md
```

Claude Code 使用 `CLAUDE.md`：

```bash
cp dist/CLAUDE.md ~/college-vault/CLAUDE.md
```

不要同时复制两个内容不同的运行文件，除非你明确知道客户端会读取哪个文件。

以后仓库中的 Prompt 有更新时，重新复制对应文件即可。重新复制不会影响 vault 中的 Markdown 资料。

## 5. 第一次打开 ZCode/Codex

在 ZCode/Codex 中打开：

```text
~/college-vault/
```

不要打开：

```text
/path/to/us-college-app-second-brain/
```

第一次可以直接发送：

> 这是我的美本申请工作区。先读取当前时间、学生时区、当前 checkpoint 和开放任务。然后告诉我工作区现在记录了什么，还缺哪些最基本的信息。不要让我一次性填完所有表格，按申请进度逐步询问。

新会话的底层读取命令是：

```bash
cd ~/college-vault
brain context --json
```

如果当前问题和某个主题有关，可以追加查询：

```bash
brain context --query "Brown 补充文书"
```

通常由 agent 自动运行这些命令，你不必每次手动运行。

## 6. 日常使用方式

### 6.1 直接用自然语言

你不需要自己维护所有 Markdown。可以直接告诉 agent：

```text
我刚刚完成了 SAT 报名，请更新任务和当前状态。以后不要再把它当成未完成事项问我。
```

```text
我想研究 Brown 的 ED 申请。先读取我的约束和已有素材，再告诉我缺哪些官网信息。
```

```text
我今天只有 40 分钟，请从开放任务中选一个最值得做的，并拆成下一步。
```

agent 应该把重要事实、素材、偏好、决定、任务和完成事件保存下来；一次性闲聊不应该污染长期资料。

### 6.2 查看当前工作状态

```bash
cd ~/college-vault
brain context
brain task list
brain task list --all
brain checkpoint show
brain validate
```

`申请追踪/总览.md` 是自动生成的查看页面。真正的任务状态在 `申请追踪/任务/*.md` 中，不要手工把总览当成唯一来源。

### 6.3 手动写入一条事实或素材

一般优先让 agent 写入。需要手动操作时：

```bash
brain remember \
  --path ~/college-vault \
  --kind experience \
  --id market-observation \
  --title "菜场观察" \
  --content "记录了 2025 年 3 月到 6 月家附近菜场改造中的摊位变化和居民反应。" \
  --source-ref "学生口述，2026-08-23"
```

常用类型：

```text
fact          学生事实
experience    经历
feeling       感受
thought       思考
relationship  关系或重要对话
preference    长期偏好
insight       用户画像中的理解或假设
```

### 6.4 管理任务和 deadline

创建任务：

```bash
brain task add \
  --path ~/college-vault \
  --id brown-why-draft \
  --title "完成 Brown 补充文书第一稿" \
  --deadline 2026-10-15 \
  --precision date_only \
  --type essay \
  --school brown \
  --round ED \
  --next-action "列出两个具体资源和个人连接"
```

`--precision` 的选择：

- `exact`：有具体日期和时刻，例如 `2026-10-15T23:59:00-04:00`
- `date_only`：只有日期，例如 `2026-10-15`
- `estimated`：大概日期或待确认日期
- `unknown`：没有 deadline

学生确认完成后：

```bash
brain task update \
  --path ~/college-vault \
  --id brown-why-draft \
  --status "已完成" \
  --completion-evidence "学生确认：第一稿已保存到申请材料目录"
```

任务逾期只表示当前时间已经超过 deadline，不表示任务自动完成。

## 7. 顾问视频转写稿知识库

知识库保存顾问观点，和学生事实分开。完整转写稿如果没有明确分发权利，默认只保存在本地。

### 7.1 准备输入文件

每个视频最好有一个一级标题：

```markdown
# 如何判断学校匹配

视频一的转写内容……

# 活动列表怎么写

视频二的转写内容……
```

输入文件可以放在 vault 外，例如 `~/Downloads/advisor-videos.md`，也可以放在：

```text
~/college-vault/knowledge/inbox/
```

`knowledge/inbox/` 和 `knowledge/sources/` 默认被 `.gitignore` 忽略。

### 7.2 先预览边界

```bash
cd ~/college-vault
brain knowledge import ~/Downloads/advisor-videos.md \
  --batch-id advisor-2026-08 \
  --advisor "顾问姓名" \
  --platform "视频平台" \
  --dry-run
```

确认输出的视频数量、标题和行号正确后正式导入：

```bash
brain knowledge import ~/Downloads/advisor-videos.md \
  --batch-id advisor-2026-08 \
  --advisor "顾问姓名" \
  --platform "视频平台"
```

如果文件用固定分隔行而不是标题：

```bash
brain knowledge import merged.txt \
  --batch-id advisor-2026-08 \
  --delimiter "===== 视频分隔 ====="
```

同一批次重新导入时保持相同 `--batch-id`，工具会同步删除该批次已经不存在的来源。

### 7.3 建立索引和搜索

不配置云端 embedding 时：

```bash
brain knowledge index
brain knowledge search "如何规划活动投入"
```

使用 OpenAI-compatible Embeddings API 时，先设置：

```bash
export BRAIN_EMBEDDING_BASE_URL="https://你的服务地址/v1"
export BRAIN_EMBEDDING_API_KEY="你的密钥"
export BRAIN_EMBEDDING_MODEL="你的模型名称"
```

然后显式允许上传顾问原文片段：

```bash
brain knowledge index --allow-remote-content
```

查询默认本地执行。确认问题已去除姓名、账号、联系方式和其他个人信息后，才允许远程查询：

```bash
brain knowledge search "已去个人信息的活动规划问题" --allow-remote-query
```

两个授权分别代表：

- `--allow-remote-content`：允许上传顾问转写内容。
- `--allow-remote-query`：允许上传查询文本。

检索结果中的 `source_id#chunk` 是引用。顾问经验必须标成顾问观点；学校官网事实、deadline 和专业要求不能只依据视频转写稿。

## 8. 逐校申请和材料

创建学校记录：

```bash
brain school add \
  --path ~/college-vault \
  --id brown \
  --name "Brown University" \
  --round ED \
  --major "Urban Studies"
```

创建申请材料：

```bash
brain artifact add \
  --path ~/college-vault \
  --id brown-why \
  --type essay \
  --version 1 \
  --status "草稿" \
  --school brown \
  --prompt "Why Brown?" \
  --limit 250 \
  --limit-unit words \
  --content-file ~/Documents/brown-why-v1.md
```

最终版必须由学生明确确认：

```bash
brain artifact add \
  --path ~/college-vault \
  --id brown-why \
  --type essay \
  --version 2 \
  --status "最终版" \
  --school brown \
  --prompt "Why Brown?" \
  --limit 250 \
  --limit-unit words \
  --student-confirmed \
  --content-file ~/Documents/brown-why-v2.md
```

查看学校是否满足提交条件：

```bash
brain school status --path ~/college-vault --id brown
```

工具会检查官方要求来源、缺口、学生确认、最终材料是否存在、材料是否是最终版以及材料是否属于该学校。文件存在或 deadline 已过都不等于可以提交。

## 9. 从 v4 迁移

迁移不修改旧 vault，目标目录必须是空目录或不存在。

先预览：

```bash
brain migrate-v4 /path/to/old-v4-vault \
  --output /path/to/new-v5-vault \
  --timezone Asia/Shanghai \
  --cycle 2027-08 \
  --dry-run
```

正式执行：

```bash
brain migrate-v4 /path/to/old-v4-vault \
  --output /path/to/new-v5-vault \
  --timezone Asia/Shanghai \
  --cycle 2027-08
brain validate --path /path/to/new-v5-vault
```

然后人工检查：

```text
学生档案/核心信息.md
申请追踪/任务/
申请追踪/学校/
申请材料/
迁移报告.md
```

旧 vault 不会被删除。无法确认的完成状态、模糊日期和文件冲突会保留为待人工确认。

## 10. 可选 ZCode hook

没有 hook 也可以使用，`AGENTS.md` 会要求 agent 在新会话读取 context。若要让 ZCode 在 SessionStart 自动注入时间、checkpoint 和开放任务：

```bash
mkdir -p ~/college-vault/.zcode
cp /path/to/us-college-app-second-brain/integrations/zcode/config.example.json \
  ~/college-vault/.zcode/config.json
```

如果已有 `.zcode/config.json`，请合并配置，不要覆盖原文件。确保：

```bash
which brain
```

能找到已安装的命令。hook 只读上下文，不会自动修改 vault。

## 11. 常见问题

### 我应该在哪个目录运行命令？

`brain` 命令可以在任意目录运行，但如果没有 `--path`，它会从当前目录向上寻找 `vault.yaml`。最不容易出错的方式是：

```bash
cd ~/college-vault
brain validate
```

### 我只复制了 AGENTS.md，可以直接用吗？

不行。`AGENTS.md` 只是运行规则，必须先安装 Python 包并运行 `brain init` 创建 vault。

### 我改了 Markdown，为什么 agent 没读到？

先运行：

```bash
brain validate
brain context --query "你刚修改的主题"
```

如果旧记录已经被新记录替代，旧记录会标记为 `superseded`，不会继续进入检索。

### 我没有 embedding API，可以用吗？

可以。`brain knowledge index` 会建立本地关键词索引，中文检索仍然可用。云端 embedding 只是可选增强。

### 能不能把真实学生资料和完整顾问转写稿推到 GitHub？

不建议，也不应默认这样做。真实 vault、API key、`knowledge/inbox/`、`knowledge/sources/` 和 `.brain/` 都应保留在本地或私有存储中。

## 12. 开发者验证

修改工具或 runtime 后，在仓库目录运行：

```bash
PYTHONPATH=src pytest
./scripts/build-dist.sh
PYTHONPATH=src python3 -m college_brain.cli validate --path templates/vault
PYTHONPATH=src python3 -m college_brain.cli validate --path examples/demo-vault
```

不要直接编辑 `dist/AGENTS.md` 或 `dist/CLAUDE.md`；它们由 `src/runtime/` 和 `scripts/build-dist.sh` 生成。
