# 问径（暂定）

把知乎中“值得看的知识与经验”，转化为可验证的真实能力。

项目当前处于黑客松立项阶段。竞赛版不做通用 AI Tutor，而是用一个垂直到底的数据库索引学习场景，证明以下闭环：

```text
诊断认知 → 给出实践 → 真实运行 → 采集 Evidence
→ 知乎观点介入 → 改变下一步任务 → 更新 Learner Model
```

核心产品判断：

> 知乎不是参考资料库，也不是传统 RAG 数据源；它提供人的经验、观点冲突和真实问题，并作为 Learning Intervention 参与学习策略。

## 当前范围

- 预算：约 50 小时 / 7 个开发日
- 主场景：数据库索引，从约 1.8s 优化到约 30ms
- 可选深度场景：并发更新与一致性，仅在主场景完成后进入
- 四个页面：Home、Diagnose、Workspace、Progress
- 一个 Runner：SQLite / SQL
- 一个 Learning Loop：Attempt → Evidence → State Update → Next Action
- 一个知乎集成：收藏入口 + 搜索观点 + 来源回链

## 项目文档

- [会话迁移与决策记录](docs/00-conversation-migration.md)
- [项目立项书](docs/01-project-charter.md)
- [MVP Backlog](docs/02-mvp-backlog.md)
- [Database Index Learning Pack](docs/03-learning-pack-database-index.md)
- [核心数据契约](docs/04-contracts.md)
- [知乎开放平台接入与 OAuth 回调](docs/05-zhihu-integration.md)

## Scope Freeze

竞赛版明确不做：通用知识图谱、任意学习主题、任意代码仓库、通用容器平台、完整终端、多 Agent、长期 Memory、社交系统、复杂知识追踪算法和桌面端深度能力。

如果进度不足，按以下顺序砍：第二个学习主题 → Knowledge Map → 桌面端 → 复杂 Learner Model → 动态课程 → 自动知识抽取。

绝不优先砍：漂亮的 Workspace、响应式 Learning Loop、真实运行、知乎参与学习、完整 Demo Story。
