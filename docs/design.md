# Architecture

v5 将职责分成四层，而不是让 Prompt 临场承担全部状态管理。

## 1. 学生数据层

Markdown 是唯一事实来源。`vault.yaml` 声明 schema、学生时区和申请季；每条长期记录使用固定 YAML frontmatter。

- `学生档案/`：学生事实
- `用户画像.md`：带来源的 AI 理解，不复制事实
- `素材库/`：原始经历和观察
- `学校研究/`：官网事实与个人匹配
- `申请追踪/`：任务和逐校状态
- `申请材料/`：版本化产物
- `状态/当前.md`：覆盖式 checkpoint
- `会话/`：追加式交接记录

## 2. 本地工具层

`src/college_brain/` 提供 `brain` CLI。Pydantic 校验记录，PyYAML 处理 Markdown frontmatter，SQLite 保存可重建索引。

工具层负责：

- 初始化和 schema 校验
- 当前时间、时区、逾期和未来事项计算
- 任务状态和完成依据
- checkpoint 和查询相关上下文
- 顾问转写导入、索引和引用检索
- v4 非破坏迁移

Prompt 负责判断“何时调用”，工具负责“如何稳定执行”。

## 3. 顾问知识层

顾问转写稿与学生 vault 的事实分开：

```text
knowledge/inbox/             原始合并文件
knowledge/sources/           一视频一来源
knowledge/catalog.yaml       来源目录
.brain/knowledge.sqlite      关键词、向量和引用索引
```

检索将本地关键词结果和 OpenAI-compatible embedding 结果用 Reciprocal Rank Fusion 合并。向量和 SQLite 都是缓存，可以从 Markdown 重建。

顾问内容只能作为二手经验。学校政策和 deadline 必须回到官网核验。

## 4. Prompt 层

`src/runtime/` 只保留项目特有协议：

- 只服务学生本人
- 会话开始与时间事件获取当前上下文
- 长期信息扫描和落盘规则
- 按任务读取相关记录
- 顾问知识检索和引用边界
- 完整申请流程与不可行边界

它不再复制模板正文，也不要求模型手写自由格式状态。

## 数据不变量

1. 学生事实只在学生档案和稳定事实记录中生效。
2. AI 判断必须带来源，不能升级成事实。
3. 顾问观点不能升级成官网事实。
4. 任务完成必须有学生确认或完成依据。
5. “逾期”“还剩几天”和 M 值都是现场计算值。
6. 申请产物必须能追溯到素材、目标和版本状态。
7. `.brain/` 删除后可以重新生成，不造成学生数据丢失。
