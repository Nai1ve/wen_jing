# MVP Backlog

## Milestone 0：立项冻结（Day 1，6h）

### M0-01 确认赛道与提交约束

- 收集截止日期、评分项、提交物、视频长度和部署要求；
- 验收：形成一页 `submission-constraints`，所有不可变约束可查。

### M0-02 知乎 API 权限 Spike

- 验证 Access Secret、`X-Request-Timestamp`、知乎搜索响应；
- 验证 OAuth、收藏夹列表与收藏内容接口是否对当前账号开放；
- 记录配额、错误码、关键字段与脱敏示例；
- 验收：`MockZhihuProvider` 与真实 Provider 能返回同一内部 schema。

### M0-03 冻结数据库索引 Demo Script

- 定义每轮 Prompt、用户选择、Runner 状态、Evidence、反馈、知乎干预与下一步；
- 至少包含“缓存误区”“单列索引不足”“联合索引”“高写入 trade-off”；
- 验收：不看代码也能从脚本完整演示 5 分钟故事。

### M0-04 冻结协议

- 定义 `LearningSession`、`Attempt`、`Evidence`、`ConceptState`、`NextLearningAction`、`KnowledgeIntervention`；
- 验收：前端可只靠 fixture 跑完整流程，后端可独立实现。

### M0-05 视觉线框

- Home、Diagnose、Workspace、Progress；
- 验收：关键状态均有页面归属，知乎卡片只在需要时出现。

## Milestone 1：可录屏的全 Mock 产品（Day 2，8h）

- M1-01 建立前端工程与视觉 tokens；
- M1-02 完成 Home 和两个挑战卡；
- M1-03 完成 Diagnose；
- M1-04 完成 Workspace 三栏或主区 + Mentor 布局；
- M1-05 完成 Progress；
- M1-06 用固定 fixtures 串联全流程；
- 验收：没有后端也能录出完整产品故事。

## Milestone 2：真实 Workspace 与 Runner（Day 3，8h）

- M2-01 SQL Editor 与预置查询；
- M2-02 SQLite 固定数据集；
- M2-03 执行、超时和只读/白名单边界；
- M2-04 `EXPLAIN QUERY PLAN`；
- M2-05 稳定 Benchmark 与测试结果；
- M2-06 前端运行状态、错误和重试；
- 验收：单列索引和联合索引产生稳定、可解释的不同 Evidence。

## Milestone 3：响应式 Learning Loop（Day 4，7h）

- M3-01 Attempt 提交；
- M3-02 Evidence 汇总；
- M3-03 结构化 LLM Evaluate；
- M3-04 Misconception 识别；
- M3-05 ConceptState 更新；
- M3-06 NextAction 选择；
- M3-07 schema 校验与 fallback；
- 验收：至少两个不同答案进入不同后续任务，且链路可在日志中解释。

## Milestone 4：知乎 Learning Intervention（Day 5，6h）

- M4-01 `ZhihuAdapter`；
- M4-02 搜索 Query 生成；
- M4-03 Question/Answer → Claim 编译；
- M4-04 Counterpoint 与 Scenario 匹配；
- M4-05 来源卡、作者、问题、原回答回链；
- M4-06 Mock/Real Provider 切换；
- 验收：知乎观点不是参考列表，而是至少一次改变 NextAction。

## Milestone 5：主场景完善（Day 6，6h）

- M5-01 完成 7～8 Round 数据；
- M5-02 补齐 5～7 Concepts 和 10 个 Misconceptions；
- M5-03 补齐 8～12 个 Perturbations；
- M5-04 精选并整理 15～20 个知乎 Claims；
- M5-05 校准 Rubric；
- 验收：数据库索引 Journey 从首次进入到结果页无断点。

## Milestone 6：只打磨，不加功能（Day 7，8h）

- M6-01 Loading、Empty、Error、Fallback；
- M6-02 动画、字体、spacing、可读性；
- M6-03 来源归属与隐私提示；
- M6-04 固定 Demo 数据和预缓存；
- M6-05 README、架构图、部署说明；
- M6-06 5 分钟 Demo 录屏；
- M6-07 Pitch 与问题清单；
- 验收：连续三次无人工修复完成 Demo。

## 第一批立即执行任务

1. 从赛道页面抄录提交约束；
2. 登录知乎开放平台，验证当前账号的 Search 与 OAuth 权限；
3. 审核并冻结现有 Database Index 8 Round Matrix；
4. 选定技术栈；
5. 审核并冻结现有六个核心 JSON 契约；
6. 画四页面低保真线框；
7. 冻结后再初始化代码工程。

## Go / No-Go 判断

第 1 天结束时，如果知乎收藏接口不可用：保留知乎搜索与来源回链，首页使用预置收藏主题或本地 fixture，不阻塞 Demo。

第 3 天结束时，如果真实 Runner 不稳定：固定 SQLite 数据集和受限 SQL 模板，禁止扩展通用执行能力。

第 5 天结束时，如果知乎真实调用不稳定：保留真实调用录像与可切换 Mock 数据，保证现场演示稳定。

任何时候主场景未完成：不启动第二个并发一致性 Pack。
