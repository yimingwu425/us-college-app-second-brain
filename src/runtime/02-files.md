# 文件与数据契约

Markdown 是学生可读、可编辑的事实载体；`.brain/` 只保存可重建索引和缓存。`vault.yaml` 的 schema 版本必须是 5。

## 唯一来源

- `学生档案/`：学生事实唯一来源，不在画像里复制姓名、年级、申请季或 M 值。
- `用户画像.md`：带来源的长期理解、主题、故事假设、偏好和未确认问题。
- `素材库/`：经历、感受、思考、关系的原始细节。
- `学校研究/<school-id>/`：学校官方事实和学生匹配分开；每条外部事实带来源和核验日期。
- `申请追踪/任务/<task-id>.md`：任务和 deadline 的唯一状态源；`申请追踪/总览.md` 是生成视图。
- `申请追踪/学校/<school-id>.md`：逐校要求、缺口和提交状态。
- `申请材料/`：版本化产物，带目标、状态、来源素材和学生确认状态。
- `状态/当前.md`：当前 checkpoint，覆盖更新，保持短。
- `会话/`：追加式会话交接和审计，不替代 checkpoint。
- `knowledge/`：独立的顾问二手知识，只读检索；不写入学生事实。

## 记录要求

长期 Markdown 记录必须有 YAML frontmatter：

```yaml
schema_version: 5
id: stable-id
type: record-type
status: active
created_at: 2026-08-22T00:00:00Z
updated_at: 2026-08-22T00:00:00Z
source_refs: []
confidence: confirmed
supersedes: []
links: []
```

学生纠正事实时更新原记录或标注 `supersedes`。同一事实不能让两条记录同时有效。引用路径必须真实存在；不能用文件名猜最新版本。

## 会话恢复

新会话先运行 `brain context --json`；按用户问题追加 `--query`。基础恢复读取：核心信息、约束与偏好、用户画像、当前 checkpoint、开放任务和 checkpoint 指定的恢复文件。只有相关任务才展开素材、学校研究和申请材料，不整库灌入上下文。

## 文件操作

优先通过 `brain` 写入和更新，避免模型手工拼出不符合 schema 的 frontmatter。修改文件后运行 `brain validate`。旧 vault 迁移使用 `brain migrate-v4`，不得覆盖旧目录。
