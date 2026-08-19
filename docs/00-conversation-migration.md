# “知乎学习 Agent 构建思路”会话迁移

## 迁移信息

- 迁移日期：2026-08-19
- 共享来源：<https://chatgpt.com/share/6a84f56a-f0cc-83ec-93a4-7b3b1324efc0>
- 原会话标题：知乎学习Agent构建思路
- 读取状态：已从当前登录态原会话读取完整正文，正文约 19,323 字符；已核对开头问题和结尾结论。
- 本文类型：语义完整迁移。去除了页面按钮、重复空行和界面噪声，保留全部立项决策、数据设计、产品流程和关键示例。

## 1. 原始问题

用户计划报名知乎黑客松，关注 AI 时代“应该学什么、有什么用、怎么用”的问题。初始产品设想是构建一个学习陪伴 Agent：以原理性理解和思考能力为目标，利用知乎优秀回答、知识干货和模型能力组织学习，但需要解决两件事：

1. 如何构建与组织知识；
2. 如何让知乎成为产品的核心，而不是顺手接入的内容源。

## 2. 产品愿景与黑客松交付物必须分开

完整愿景包含动态课程生成、Learner Model、知乎知识组织、Argument Graph、代码执行环境、响应式学习策略和桌面端，属于至少 2～3 个月的产品原型工作量。

黑客松只需证明：新的学习范式成立，并且用户能在 5 分钟 Demo 中感受到。

建议竞赛预算：40～60 小时，目标锁定约 50 小时。

黑客松只证明这条链：

```text
用户想学一个工程知识
→ AI 判断当前认知状态
→ 给出实践任务
→ 用户思考或修改代码
→ 真实运行
→ 获得 Evidence
→ AI 根据 Evidence 改变下一步任务
→ 知乎观点、原理或工程经验介入
→ Learner Model 更新
```

竞赛版不做：

- 通用 Knowledge Graph；
- 自动构建整个领域课程；
- Argument Graph 可视化；
- 任意 GitHub Repo；
- 任意语言执行；
- 完整 Terminal 或 Docker 云 IDE；
- 多 Agent、长期 Memory、社交系统；
- Tauri 深度能力；
- 复杂个性化推荐与 Bayesian Knowledge Tracing。

## 3. 主题选择与 Scope Freeze

首页可以表达“你想学什么”，但 Demo 只精心支持 1～2 个 Learning Journey。

### Journey A：数据库索引

```text
Predict → EXPLAIN → 添加索引 → Benchmark
→ 发现联合索引问题 → Optimize → Trade-off
```

优点是反馈直观，首次使用者几乎不需要学习产品操作。典型结果从约 1800ms 降到约 30ms。

### Journey B：并发问题

```text
Predict → Race Condition → Run → FAIL
→ Fix with Lock → PASS → Perturbation → Distributed Case
```

它适合通过不断改变约束来展示响应式学习，但只在数据库索引场景完成后实现。

最终 Scope Freeze：一个场景、一个 Learning Loop、一个 Runner、一个知乎集成、四个页面。实现路径垂直切到 Software Engineering → Database → Index。

## 4. 约 50 小时的资源分配

| 模块 | 预算 | 交付 |
|---|---:|---|
| 产品与交互原型 | 5h | 完整 Demo Story、信息架构、数据库索引脚本 |
| 前端视觉框架 | 10h | Sidebar、Workspace、Mentor、Editor、Result、Progress、Zhihu Card |
| Learning Loop | 8h | submit → evaluate → update → next |
| Code Runner | 6h | SQLite/SQL 执行、EXPLAIN、Benchmark、Metrics |
| 知乎 API | 5～8h | 搜索、来源、Claim 提取、Learning Intervention |
| Learner Model | 4h | 简化的多维 ConceptState 与 Evidence 更新 |
| Polish + Demo | 10h | 动效、异常、空状态、Fallback、录屏、Pitch、README |

AI 编程可以压缩 CRUD 与 UI 搭建，但产品交互、集成、Debug、视觉细节和 Demo 打磨无法同比例压缩，因此最后 10 小时必须保留。

## 5. 七天推进节奏

### Day 1：把产品拍死（6h）

确定 Demo Story、信息架构、页面 Wireframe、数据协议和数据库索引 Journey。当天结束必须能回答：评委从点击 Start 到最后看到什么？

### Day 2：前端外壳（8h）

用 Mock Data 完成 Home、Diagnose、Workspace、Progress，先达到可录产品视频的视觉完成度。

### Day 3：Workspace（8h）

完成 Monaco、Run、Result、Mentor Feedback、Next Action；做到“写 SQL → Run → 页面状态变化”。

### Day 4：Learning Engine（7h）

把 Fake 状态替换为 Attempt → LLM Evaluate → Evidence → LearnerState → NextAction，并让两个不同回答产生不同后续任务。

### Day 5：知乎（6h）

接入 Search → Source → Extract → Display，至少确保一次知乎观点真正改变 Learning Action。

### Day 6：完善主场景（6h）

主场景不丝滑就不开发第二个场景。只有数据库索引完成，才考虑并发一致性。

### Day 7：禁止加功能（8h）

只允许 Bugfix、视觉、动效、Fallback、Demo、Pitch、录屏和 README。

## 6. 两套高度策划的 Learning Pack

数据层不建设“软件工程知识库”，而建设两个 Learning Pack：

| Pack | 作用 | 主题 |
|---|---|---|
| Quick Win | 低门槛、5～10 分钟看到效果 | SQL 慢查询与索引优化 |
| Deep Dive | 证明系统能训练工程判断 | 并发更新 → 事务 → 幂等 → 一致性 |

两个 Pack 同属后端工程，可复用数据库、Runner、评测体系和部分知识数据。

### Pack 01：Database Index

核心 Journey：

1. Predict：判断慢 SQL 的问题；
2. Observe：真实执行，看到 Full Table Scan 和约 1834ms；
3. Action：创建 `user_id` 单列索引；
4. Feedback：降到约 287ms，继续追问为什么仍未达标；
5. Zhihu Intervention：引入“不要脱离查询模式设计索引”的工程观点；
6. Fix：创建 `(user_id, created_at DESC)` 联合索引；
7. Perturbation：加入每秒 5 万写入，迫使用户思考索引维护成本与 trade-off。

### Pack 02：Concurrency & Consistency

核心能力链：

```text
Race Condition → Thread Lock → Database Transaction
→ Isolation Level → Optimistic/Pessimistic Lock
→ Retry → Idempotency → Distributed Consistency
```

典型场景：最后 10 件库存、100 个并发请求。用户先用本地 Lock 通过单实例测试，系统随后把部署条件改成 5 个实例，让旧方案失效。接着引入 Redis Lock、`SELECT ... FOR UPDATE`、Atomic Update、Optimistic Lock 等观点，让用户说明成立条件。再通过请求重试和跨服务超时进入幂等与补偿。

## 7. 真正的数据资产是 Learning Dataset

不要搜数百篇回答后直接做 embedding + RAG。每个 Pack 需要组织：

```yaml
topic: database_index
concepts:
  - full_table_scan
  - single_column_index
  - composite_index
  - covering_index
  - write_amplification
misconceptions:
  - 查询慢就加缓存
  - WHERE 的列全部建索引就行
  - 索引越多越好
  - 联合索引只是多个单列索引
cases:
  - slow_user_orders_query
  - high_write_orders_table
actions:
  - predict
  - diagnose
  - modify
  - compare
  - transfer
evidence:
  - explain_plan
  - runtime
  - test_result
  - reasoning
  - solution_choice
```

每个 Concept 准备四类信息：Canonical Knowledge、Misconception、Case/Perturbation、Rubric/Evidence。

推荐三层数据架构：

```text
Source Layer
知乎回答 / 官方文档 / Case
        ↓
Knowledge Layer
Concept / Claim / Misconception / Principle / Trade-off
        ↓
Learning Layer
Task / Action / Evidence / Perturbation / Rubric
```

### 建议数据规模

Database Index：5～7 Concepts、10 个 Misconceptions、3 个 Case、8～12 个 Perturbations、15～20 条精选知乎 Claims、约 20 个 Learning Actions。

Concurrency & Consistency：8～10 Concepts、12～15 个 Misconceptions、4 个 Case、15～20 个 Perturbations、20～30 条精选知乎 Claims、约 30 个 Learning Actions。

真正需要精读的知乎内容总量可控制在 50 篇以内。耗时重点是把内容组织成学习行为，而不是抓取规模。

## 8. 知乎在产品中的定位

知乎不是教材库，也不是 RAG 数据源。三方分工：

- 知乎：人的知识、经验、观点冲突和真实问题；
- AI：Adaptive Learning Policy；
- Practice Environment：Objective Evidence；
- 最终目标：User Real Capability。

产品核心叙事：

> 知乎解决“世界上有哪些值得看的知识与经验”，AI 解决“这些知识此刻应该怎样进入你的学习过程”，实践环境解决“你到底有没有学会”。

这与“知乎 + RAG + AI Tutor”不同。

## 9. 知乎的三个入口

### 入口一：我的收藏

把“看到好回答 → 收藏 → 再也不看”翻转为：

```text
知乎收藏 → 识别学习意图 → Learning Backlog
→ 诊断是否掌握 → 生成实践 → 形成能力
```

收藏、关注和创作只作为 Learner Model 的 prior：收藏过不等于学会，写过不等于精通，关注过不等于理解。

### 入口二：学习过程中的动态搜索

不是传统 Top-K RAG，而是：

```text
Current Learning State
→ 判断缺少哪种刺激
→ 生成知乎 Query
→ 搜索 Question/Answers
→ Claim Extraction
→ 匹配 Misconception
→ Learning Intervention
```

### 入口三：观点冲突

专门寻找支持、反对、限定条件、真实案例和踩坑，形成 Argument Set。用户必须选择观点并解释成立条件，而不是让 AI 给出唯一最佳实践。

## 10. 知乎的三种呈现时机

| 时机 | 呈现 | 目的 |
|---|---|---|
| 学习前 | 收藏、关注、创作 | 发现“我曾经想学什么” |
| 学习中 | 观点卡、反例、工程经验 | 改变当前思考和下一道题 |
| 学习后 | 来源与延伸阅读 | 回到原始讨论深入阅读 |

知乎不应永久占据 Sidebar。它只在对当前学习有意义时出现，体现“响应式”。

最适合 Demo 的一幕：用户用 Redis Lock 通过测试，系统捕获 Evidence；知乎观点卡提出“库存就在 MySQL，为什么再引入 Redis”，随后生成“不用 Redis 实现相同一致性保证”的新挑战。

关键 Pitch：

> 它不是参考资料。它参与 Learning Policy。

## 11. 后台抽象

不要实现 `ZhihuRAG`，而是实现：

```text
ZhihuAdapter
  search(query)
  search_user_collections(...)
  get_following(...)
  get_creations(...)
  zhida(...)
  get_hotlist(...)
```

其上是 Knowledge Compiler：

```text
Question / Answer
→ normalize
→ Concept / Claim / Reason / Example
→ Counterpoint / Scenario / Source
→ KnowledgeIntervention
```

Learning Engine 只依赖规范化的 `KnowledgeIntervention`，不直接依赖知乎 API。

```json
{
  "type": "counterpoint",
  "concept": "distributed_lock",
  "claim": "数据库原子操作可能已经足够解决该问题",
  "reason": "...",
  "source": {
    "provider": "zhihu",
    "question": "...",
    "answer": "...",
    "author": "..."
  }
}
```

## 12. 知乎能力优先级

| 能力 | 优先级 | 用途 |
|---|---|---|
| 我的收藏 | P0 | 个性化学习入口 |
| 知乎搜索 | P0 | 实时寻找观点与案例 |
| 回答与来源信息 | P0 | Claim provenance 与回链 |
| 知乎直答 | P1 | Query 理解和知识发现 |
| 我的创作 | P1 | Learner prior |
| 我的关注 | P1 | 兴趣领域 prior |
| 热榜 | P2 | 今日挑战 |
| 全网搜索 | P2 | MVP 暂不使用，避免稀释“为什么是知乎” |

## 13. 首页与 5 分钟 Demo 叙事

首页暂定项目名“问径”，文案：“把你收藏过的知识，真正变成你的能力。”

授权后，系统从收藏中识别数据库工程、Agent、Kubernetes、系统设计等主题，找出“收藏多但无学习记录”的领域，并发起 10 分钟挑战。

Demo 主链：

```text
我的知乎
→ 发现数据库工程学习目标
→ 诊断慢 SQL
→ 真实执行约 1.8s
→ 用户添加单列索引
→ 降到约 287ms
→ 知乎工程观点介入
→ 用户设计联合索引
→ 降到约 30ms
→ 加入高写入约束
→ 用户重新判断 Trade-off
→ 显示能力维度增长
→ 回到知乎原回答继续探索
```

结束页显示：Composite Index 的 Application 与 Trade-off 等维度变化，以及本次使用的知乎回答、工程观点和相反判断数量。

## 14. 当前最重要的数据工作

除了两个 Learning Pack，还需单独定义 `Zhihu Intervention Dataset`：

- 什么用户状态触发干预；
- 应找哪一种知乎内容；
- 生成什么 Query；
- 提取什么 Claim、Reason、Counterpoint 与 Scenario；
- 以什么 Learning Action 重新交给用户；
- 用什么 Evidence 判断干预是否有效。

这可能是黑客松最值得展示的知乎创新点。

## 15. 接口核对结果

2026-08-19 读取知乎开放平台文档入口后，可见文档目录包括：知乎搜索 API/Skill/MCP、全网搜索 API/Skill/MCP、直答 API/Skill/MCP、热榜 API/Skill/MCP、知识库接口、OAuth，以及用户内容、关注、收藏、收藏夹相关 API。

鉴权页说明数据接口推荐使用 `Authorization: Bearer <your_access_secret>`，并要求 `X-Request-Timestamp` 秒级 Unix 时间戳。示例接口为：

```text
GET https://developer.zhihu.com/api/v1/content/zhihu_search
```

立项阶段仍需在黑客松账号中确认实际权限、配额、响应 schema、OAuth 回调配置与收藏接口可用性。不得把文档目录可见等同于账号已经获权。

## 16. 尚未拍板的决策

1. 前后端技术栈与部署平台；
2. 黑客松截止日期与每日可投入时间；
3. 赛道具体评分项和提交物要求；
4. 知乎开发者账号已经开通的 API 与 OAuth 权限；
5. LLM 提供方、结构化输出与成本预算；
6. SQLite 数据规模、稳定 Benchmark 方法与服务端安全边界；
7. 是否保留第二个并发场景；
8. UI 视觉方向和品牌名“问径”是否最终采用。
