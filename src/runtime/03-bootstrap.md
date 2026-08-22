# 初始化学生工作区

学生端需要先安装本仓库的本地工具，然后在空目录运行：

```bash
brain init --timezone Asia/Shanghai --cycle YYYY-MM
```

`brain init` 会创建 v5 结构；已有目录不覆盖。若用户只复制了 `AGENTS.md` 而没有安装工具，应明确告诉他先安装本地包，不要假装已经完成初始化。

## 结构

```text
vault.yaml
学生档案/
  核心信息.md
  学业与课程.md
  标化考试.md
  荣誉.md
  约束与偏好.md
用户画像.md
素材库/经历/  素材库/感受/  素材库/思考/  素材库/关系/
学校研究/<school-id>/
申请追踪/任务/
申请追踪/学校/
申请追踪/总览.md
申请材料/CommonApp/  申请材料/活动列表/  申请材料/荣誉列表/
申请材料/文书/  申请材料/推荐信/
状态/当前.md
会话/
knowledge/inbox/  knowledge/sources/  knowledge/topics/
.brain/
```

启动后不要逼学生填完全部字段。可以让学生提供基本信息，也可以直接从当前最烦或最想解决的问题开始；但时区和申请季是计算时间时必须确认的基准。
