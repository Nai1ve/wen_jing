# 问径：知乎学习 Agent 项目立项书

## 1. 项目定义

一句话：将知乎收藏与真实工程观点编译成响应式实践任务，用可执行结果证明用户是否真正学会。

项目阶段：知乎黑客松 Competition MVP。

暂定周期：7 个开发日，约 50 小时。

## 2. 问题

AI 降低了获取答案的成本，但用户仍不知道应该学什么、知识在什么情境下有用、以及自己是否真的会用。传统收藏夹解决“保存”，教程解决“讲解”，普通 AI Tutor 解决“问答”，但它们很少利用真实 Evidence 验证能力，也很少让人的经验与观点冲突改变学习路径。

## 3. 核心假设

1. 用户过去在知乎的收藏、关注和创作可以作为学习意图的 prior，但不能代表掌握；
2. 真实运行结果比主观自评更适合作为学习 Evidence；
3. 知乎内容在识别到误区或工程分歧时介入，比常驻资料列表更有价值；
4. 一个完整、垂直的 Learning Journey 足以在黑客松中证明范式，无需通用化。

## 4. 目标与成功标准

### 产品目标

- 用户在 10 分钟内完成一次从诊断、实践、知乎干预到能力更新的闭环；
- 评委在 5 分钟 Demo 内能清楚回答“为什么必须是知乎”；
- 至少两个不同用户决策会产生不同的下一步任务；
- 至少一次知乎 Claim 直接改变当前 Learning Action；
- SQL Runner 返回真实执行计划、耗时和评测结果；
- 所有知乎观点都保留来源与回链。

### Demo 验收指标

- 从首页到结果页全流程无需手工修复数据；
- 慢 SQL、单列索引、联合索引三个阶段的结果稳定可复现；
- LLM 失败时有固定结构化 fallback；
- 无知乎 API 时可切换 Mock Provider，Demo 不被外部接口拖死；
- 核心路径在正常网络下 5 分钟内完成。

## 5. 核心用户流程

```text
连接知乎或选择预置主题
→ 生成 Learning Backlog
→ 进入数据库索引挑战
→ 预测与解释
→ 执行慢 SQL
→ 修改索引并再次运行
→ 捕获 Evidence
→ 识别 Misconception
→ 知乎 Counterpoint 介入
→ 生成下一道挑战
→ 更新 ConceptState
→ 来源回链与延伸阅读
```

## 6. MVP 功能范围

### P0

- Home：项目叙事、知乎连接入口、预置挑战入口；
- Diagnose：初始判断与认知诊断；
- Workspace：SQL Editor、Run、执行计划、耗时、Mentor Panel；
- Progress：ConceptState 变化、Evidence、来源；
- Database Index Learning Pack；
- SQLite Runner；
- Learning Engine 的结构化输入输出；
- `MockZhihuProvider` 与 `ZhihuProvider` 统一 Adapter；
- `KnowledgeIntervention` 规范化协议；
- 来源卡与原回答回链；
- Demo 数据、失败兜底、录屏与 Pitch。

### P1

- 读取收藏并编译 Learning Backlog；
- 知乎直答辅助 Query 理解；
- 用户创作与关注作为 prior；
- 并发一致性 Pack 的最小切片。

### P2 / 非本次范围

- 热榜挑战、全网搜索；
- 通用知识图谱、自动课程、多主题市场；
- 复杂 Argument Graph、长期学习记忆；
- 通用沙箱、任意 Repo、桌面端。

## 7. 建议系统边界

```text
Web Client
  Home / Diagnose / Workspace / Progress
              │
              ▼
Learning API
  Session / Attempt / Evidence / LearnerState
              │
       ┌──────┴────────┐
       ▼               ▼
Learning Engine      SQL Runner
       │               │
       ▼               ▼
KnowledgeIntervention  Plan / Runtime / Tests
       ▲
       │
Knowledge Compiler
       ▲
       │
ZhihuAdapter
  Mock / Search / OAuth User Data
```

Learning Engine 不依赖知乎原始响应，只依赖规范化 `KnowledgeIntervention`；Runner 不依赖 LLM；前端可在后端未完成时完全使用 Mock 数据。

## 8. 最小领域模型

```text
LearningSession
LearningPack
LearningAction
Attempt
Evidence
ConceptState
Misconception
Perturbation
KnowledgeIntervention
SourceAttribution
```

建议 `ConceptState` 维度：understanding、application、diagnosis、design、tradeoff、transfer。黑客松阶段使用可解释的离散等级，不引入复杂概率模型。

## 9. 主要风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 知乎账号权限或 API 不稳定 | 核心集成阻塞 | Adapter + Mock Provider；Day 1 完成权限 Spike |
| LLM 输出不稳定 | 学习路径失控 | JSON Schema、校验、固定 fallback、预缓存 |
| SQLite Benchmark 波动 | Demo 证据不可信 | 固定数据集、warm-up、重复测量、区间显示 |
| 需求膨胀 | 无法完成 | Scope Freeze；Day 7 禁止新增功能 |
| UI 先后顺序不当 | 到最后没有可展示产品 | Day 2 先完成全 Mock 外壳 |
| 知乎变成普通 RAG | 失去赛道差异 | 验收要求：知乎内容必须至少一次改变 Next Action |
| 第二场景分散资源 | 主链不完整 | 主场景未通过验收前不启动 |

## 10. 立项 Gate

进入正式编码前，需要完成四个 Gate：

1. Demo Script Freeze：数据库索引 7～8 Round 全部拍板；
2. Contract Freeze：Attempt、Evidence、NextAction、KnowledgeIntervention schema 拍板；
3. API Spike：确认知乎鉴权、搜索、收藏和来源字段；
4. Visual Checkpoint：四页面低保真线框与关键状态拍板。

Gate 未完成时，只允许做最小技术验证，不启动大规模工程搭建。
