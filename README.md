# 美本申请第二大脑 v5

这是一个给学生自己使用的美本申请工作区。你用自然语言和 ZCode/Codex 对话，资料以 Markdown 保存在本地；`brain` 是配套的本地命令行工具，负责读取资料、记录时间、管理任务、搜索顾问知识和检查数据是否完整。

它不是网申自动提交器，也不是家长、顾问或中介的协作系统。

## 先理解两个目录

第一次使用最容易混淆的地方是：**GitHub 仓库和学生工作区不是同一个目录。**

```text
GitHub 仓库（安装工具、提供 Prompt）
  /你的路径/us-college-app-second-brain/

学生工作区（真正保存你的申请资料）
  ~/college-vault/
```

- GitHub 仓库可以更新、重新下载，也可以删除后重新安装。
- 学生工作区包含你的个人资料、素材、任务、文书和会话记录，应该单独备份。
- 以后打开 ZCode/Codex 时，要打开**学生工作区**，不是仓库目录。
- 顾问视频转写稿也放在学生工作区的 `knowledge/` 中，不要放进公开 GitHub 仓库。

## 五分钟开始使用

### 1. 下载并安装本地工具

在终端执行：

```bash
git clone https://github.com/yimingwu425/us-college-app-second-brain.git
cd us-college-app-second-brain
python3 --version
python3 -m pip install -e .
brain --help
```

Python 需要 3.11 或更高版本。

### 2. 创建学生工作区

下面的时区和申请季请按你的实际情况修改。`--cycle` 表示申请季开始月份，例如 2027 年 8 月写成 `2027-08`。

```bash
brain init ~/college-vault \
  --timezone Asia/Shanghai \
  --cycle 2027-08
```

如果你在美国生活，时区可以写成例如 `America/New_York`。不确定时先不要猜，创建后在 `vault.yaml` 中确认。

### 3. 安装学生端 Prompt

ZCode/Codex 使用 `AGENTS.md`，Claude Code 使用 `CLAUDE.md`。只复制你实际使用的那一个即可：

```bash
cp dist/AGENTS.md ~/college-vault/AGENTS.md
# 如果使用 Claude Code，则改为：
# cp dist/CLAUDE.md ~/college-vault/CLAUDE.md
```

检查工作区：

```bash
cd ~/college-vault
brain validate
brain doctor
```

看到 `校验通过` 后，说明本地工作区可以使用。

### 4. 在正确的目录打开 ZCode/Codex

在 ZCode/Codex 中打开 `~/college-vault/`，然后直接说：

> 从今天开始帮我管理美本申请。先读取当前时间、当前状态、核心档案和开放任务，然后告诉我现在最重要的下一步。不要让我一次性填完整问卷，缺什么时再逐项问我。

你不需要先手工填写所有 Markdown。之后你可以直接说：

- “我刚刚想到一段可以用于主文书的经历，帮我保存并判断应该放在哪里。”
- “我已经完成了 SAT 报名，更新任务，不要下次再问我。”
- “帮我比较 Brown 和 Yale，但学校截止日期必须查官网。”
- “我今天只有 30 分钟，按当前任务给我一个最小可执行计划。”

Prompt 会要求 agent 在对话结束时扫描值得长期保存的信息，并在需要时调用 `brain` 写入文件。

## 日常怎么用

通常不需要自己输入下面的命令，ZCode/Codex 会根据 `AGENTS.md` 调用。遇到问题时可以手动运行。

### 查看当前状态

```bash
cd ~/college-vault
brain context --json
brain context --query "Brown 补充文书"
brain task list
brain checkpoint show
```

`brain context` 会读取当前时间、学生时区、checkpoint、开放任务和与问题相关的文件。它不会把整个 vault 一次性塞给模型。

### 手动记录长期信息

```bash
brain remember \
  --kind fact \
  --id english-test-date \
  --title "英语考试计划" \
  --content "计划在 2026-10-12 参加考试。" \
  --source-ref "学生在 2026-08-23 对话中确认"
```

常用 `--kind`：

- `fact`：学生事实
- `experience`：经历素材
- `feeling`：感受
- `thought`：思考
- `relationship`：关系或对话
- `preference`：长期偏好
- `insight`：带来源的画像判断

优先让 agent 记录，因为它会同时判断文件位置、来源和是否需要替代旧记录。

### 管理任务

创建任务：

```bash
brain task add \
  --id brown-why-draft \
  --title "完成 Brown 补充文书第一稿" \
  --deadline 2026-10-15 \
  --precision date_only \
  --type essay \
  --school brown \
  --round ED \
  --next-action "先列出两个具体资源和个人连接"
```

学生明确说已经完成时，必须带完成依据：

```bash
brain task update \
  --id brown-why-draft \
  --status "已完成" \
  --completion-evidence "学生确认：已完成并保存最终稿"
```

截止日期已过不等于任务完成。日期只有大概范围时使用 `estimated`，只有日期没有具体时刻时使用 `date_only`，不要编造精确时间。

### 检查 vault

```bash
brain validate
brain doctor
```

修改 Markdown 后如果出现读取异常，先运行 `brain validate`，按错误路径修复；不要直接删除 `.brain/` 以外的资料。`.brain/` 是可重建缓存，必要时可以删除后重新索引。

## 导入顾问视频转写稿

顾问知识和你的个人资料是分开的。完整转写稿默认是私有内容，不要提交到公开 GitHub。

### 1. 准备转写稿

合并 TXT/Markdown 中，最好用一级标题区分视频：

```markdown
# 第一个视频标题

第一个视频的转写内容……

# 第二个视频标题

第二个视频的转写内容……
```

如果使用固定分隔行，也可以在导入时传 `--delimiter`。先只预览，不写入文件：

```bash
cd ~/college-vault
brain knowledge import ~/Downloads/advisor-videos.md \
  --batch-id advisor-2026-08 \
  --advisor "顾问姓名" \
  --platform "视频平台" \
  --dry-run
```

确认识别的视频标题和数量正确后，正式导入：

```bash
brain knowledge import ~/Downloads/advisor-videos.md \
  --batch-id advisor-2026-08 \
  --advisor "顾问姓名" \
  --platform "视频平台"
```

同一批次以后重新导入时继续使用同一个 `--batch-id`。这样删除的旧视频也会从该批次的来源和索引中清理。

### 2. 建立检索索引

不配置云端服务也能使用中文关键词检索：

```bash
brain knowledge index
brain knowledge search "活动规划如何判断投入产出"
```

如果要使用 OpenAI-compatible Embeddings API，先在当前终端设置环境变量：

```bash
export BRAIN_EMBEDDING_BASE_URL="https://你的服务地址/v1"
export BRAIN_EMBEDDING_API_KEY="你的密钥"
export BRAIN_EMBEDDING_MODEL="你的 embedding 模型"
```

然后明确允许上传顾问转写片段建立向量：

```bash
brain knowledge index --allow-remote-content
```

查询默认仍然只用本地关键词。只有确认查询已经去掉姓名、账号、联系方式和其他个人信息时，才使用：

```bash
brain knowledge search "已去个人信息的选校问题" --allow-remote-query
```

`--allow-remote-content` 会上传顾问原文片段；`--allow-remote-query` 会上传查询文本。两者是独立授权。学校政策、专业要求和截止日期仍必须以当前官网为准，顾问视频只能作为经验观点。

## 从 v4 迁移旧资料

迁移会创建新目录，不会覆盖或删除旧 vault。

先预览：

```bash
brain migrate-v4 \
  /path/to/old-v4-vault \
  --output /path/to/new-v5-vault \
  --cycle 2027-08 \
  --dry-run
```

确认报告后正式迁移：

```bash
brain migrate-v4 \
  /path/to/old-v4-vault \
  --output /path/to/new-v5-vault \
  --timezone Asia/Shanghai \
  --cycle 2027-08

brain validate --path /path/to/new-v5-vault
```

迁移完成后人工检查：

1. `学生档案/核心信息.md`
2. `申请追踪/任务/`
3. `申请追踪/学校/`
4. `申请材料/`
5. `迁移报告.md`

旧日期精度不明确、旧任务完成状态没有证据或旧文件结构无法判断的内容，会在报告中标为待人工确认。

## 可选：配置 ZCode SessionStart hook

不配置 hook 也能使用，`AGENTS.md` 会要求 agent 在新会话开始时调用 `brain context --json`。如果希望 ZCode 自动注入当前时间和 checkpoint：

```bash
cd /path/to/us-college-app-second-brain
mkdir -p ~/college-vault/.zcode
cp integrations/zcode/config.example.json ~/college-vault/.zcode/config.json
```

如果工作区已经有 `.zcode/config.json`，不要直接覆盖，把示例中的 `SessionStart` hook 合并进去。确保 `brain` 已安装且在 PATH 中。hook 只读上下文，不会自动修改学生资料。

## 工作区主要文件

```text
vault.yaml                 时区、申请季和 schema 版本
AGENTS.md                  学生端运行规则
学生档案/                  学生事实
素材库/                    经历、感受、思考和关系素材
学校研究/                  学校事实与个人匹配
申请追踪/任务/             任务和 deadline 的唯一状态源
申请追踪/学校/             每所学校的缺口和提交状态
申请材料/                  Common App、活动、文书等版本
状态/当前.md               当前 checkpoint
会话/                      会话交接记录
knowledge/                 顾问知识库
.brain/                    可重建的 SQLite 索引和缓存
```

Markdown 是事实来源。不要把 `.brain/` 当成资料备份，也不要把真实学生 vault、API key 或完整顾问转写稿提交到公开仓库。

## 进一步阅读

- [完整安装和配置](docs/setup.md)
- [设计说明](docs/design.md)
- [ZCode hook 示例](integrations/zcode/README.md)
- [虚构 demo vault](examples/demo-vault/)
- [自动测试](tests/)

## License

项目代码和原创文档使用 `CC BY-NC-SA 4.0`，见 [LICENSE.md](LICENSE.md)。第三方视频转写稿不自动获得本项目许可，公开或分发前必须单独确认权利。
