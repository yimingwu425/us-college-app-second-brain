# 美本申请第二大脑 v5

美本申请第二大脑是一套只面向学生本人的 Prompt + 本地工具。学生用自然语言与 ZCode/Codex 沟通，资料保存在自己可读、可修改的 Markdown 工作区；`brain` CLI 负责时间、任务状态、可靠存取、顾问知识检索、校验和旧数据迁移。

它不是网申代提交工具，也不是家长、顾问或中介的多人协作系统。

## 解决什么

- **可靠记忆**：把学生事实、经历素材、AI 判断和申请产物分开保存，并按问题取回相关记录。
- **真实时间**：每个新会话读取当前时间；任务完成、延期或出现相对日期时重新计算。
- **任务状态**：学生说“做完了”后，同轮更新任务与 checkpoint，不再继续把它当未完成事项追问。
- **顾问知识库**：把合并的 TXT/Markdown 视频转写稿拆成独立来源，通过关键词和可选云端 embedding 检索，并返回可追溯引用。
- **完整申请流程**：覆盖建档、素材、活动、选校、Common App、逐校申请、提交检查和申请后事项。
- **数据可带走**：Markdown 是唯一事实来源；SQLite 只保存可重建索引。

## 安装

需要 Python 3.11 或以上版本。

```bash
cd us-college-app-second-brain
python3 -m pip install -e .
```

创建学生工作区：

```bash
brain init ~/college-vault --timezone Asia/Shanghai --cycle 2027-08
cp dist/AGENTS.md ~/college-vault/AGENTS.md
cd ~/college-vault
brain doctor
```

然后在该目录打开 ZCode/Codex。学生可以直接说当前最想解决的事，不需要先填完整问卷。

完整安装说明见 [docs/setup.md](docs/setup.md)，架构见 [docs/design.md](docs/design.md)。

## 日常命令

通常由 agent 根据 `AGENTS.md` 自动调用；学生也可以手动检查：

```bash
brain context --query "Brown 补充文书"
brain task list
brain checkpoint show
brain knowledge search "ED 选校策略"
brain knowledge search "已去个人信息的 ED 选校策略" --allow-remote-query
brain validate
```

## 导入顾问视频转写稿

原稿默认是私有资料，不进入公开仓库。先预览视频边界：

```bash
brain knowledge import /path/to/merged.md --dry-run
brain knowledge import /path/to/merged.md --advisor "顾问名"
```

建立检索索引：

```bash
export BRAIN_EMBEDDING_BASE_URL="https://api.example.com/v1"
export BRAIN_EMBEDDING_API_KEY="..."
export BRAIN_EMBEDDING_MODEL="embedding-model"
brain knowledge index --allow-remote-content
```

未配置 embedding 或不加远程授权标志时，中文关键词检索仍可使用。`--allow-remote-content` 会把顾问转写片段发送给配置的 embedding 服务；`--allow-remote-query` 会发送已去个人信息的查询。转写稿是顾问二手观点；学校政策、专业要求和 deadline 仍需核对当前官网。

## 从 v4 迁移

迁移永远写入新目录，不覆盖旧 vault：

```bash
brain migrate-v4 /path/to/old-vault --output /path/to/new-vault --dry-run
brain migrate-v4 /path/to/old-vault --output /path/to/new-vault --cycle 2027-08
brain validate --path /path/to/new-vault
```

迁移后会生成 `迁移报告.md`。无法确认的旧状态不会擅自标成完成。

## 仓库结构

```text
src/college_brain/       本地 CLI、数据模型、迁移与检索
src/runtime/             学生端运行规则源文件
src/manifest.md          runtime 构建顺序
scripts/build-dist.sh    校验模板并生成 dist
schemas/                 v5 数据契约说明
integrations/zcode/      可选 ZCode SessionStart 集成
examples/demo-vault/     虚构学生 v5 样例
templates/vault/         brain init 生成的参考模板
evals/                   模型行为回归用例
tests/                   自动测试
```

维护时修改 `src/runtime/` 和 `src/college_brain/`，然后运行：

```bash
pytest
./scripts/build-dist.sh
```

不要直接编辑 `dist/`。

## License

项目代码和原创文档使用 `CC BY-NC-SA 4.0`，见 [LICENSE.md](LICENSE.md)。第三方视频转写稿不自动获得本项目许可，公开或分发前必须单独确认权利。
