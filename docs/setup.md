# Setup

## 安装本地工具

需要 Python 3.11+：

```bash
cd us-college-app-second-brain
python3 -m pip install -e .
brain --help
```

## 新建学生工作区

```bash
brain init ~/college-vault --timezone Asia/Shanghai --cycle 2027-08
cp dist/AGENTS.md ~/college-vault/AGENTS.md
cd ~/college-vault
brain doctor
```

`--cycle` 是开始递交申请的月份，不等同于当前年级。学生时区如果还未确认，`vault.yaml` 会保留 `timezone_confirmed: false`，agent 应在涉及相对日期前确认。

## ZCode/Codex

在学生 vault 根目录启动 ZCode/Codex。`AGENTS.md` 要求每个新会话先调用：

```bash
brain context --json
```

可选的 ZCode SessionStart hook 示例在 `integrations/zcode/`。核心流程不依赖 hook；没有 hook 时由 AGENTS 规则调用 CLI。

## Embedding 配置

顾问知识库支持 OpenAI-compatible Embeddings API：

```bash
export BRAIN_EMBEDDING_BASE_URL="https://api.example.com/v1"
export BRAIN_EMBEDDING_API_KEY="..."
export BRAIN_EMBEDDING_MODEL="embedding-model"
```

API Key 不写入仓库或 vault。学生个人资料不自动发送到 embedding 服务。索引默认只建本地关键词；只有显式添加 `--allow-remote-content` 才会把顾问知识片段发送到 embedding 接口。查询默认使用本地关键词检索，只有显式添加 `--allow-remote-query` 才会把已去个人信息的问题发送到接口。

## 导入转写稿

合并 TXT/Markdown 中每个视频应使用一级/二级标题或明确分隔符：

```bash
brain knowledge import merged.md --dry-run
brain knowledge import merged.md --advisor "顾问名" --platform "平台"
brain knowledge index --allow-remote-content
brain knowledge search "活动规划如何判断投入产出"
brain knowledge search "已去个人信息的活动规划问题" --allow-remote-query
```

导入预览会显示标题、来源 ID 和原文行号。版权未确定时，`knowledge/inbox/`、`knowledge/sources/` 和 `.brain/` 默认不进入 Git。

## 校验与迁移

```bash
brain validate
brain doctor
brain migrate-v4 old-vault --output new-vault --dry-run
```

迁移不覆盖旧目录。完成迁移后先运行 `brain validate --path new-vault`，再人工检查迁移报告、学生核心事实、开放任务和当前申请材料。
