# Learning Pack 01：Database Index

## Pack 目标

让用户通过一条可执行的慢查询优化链，形成以下能力：

- 能从查询访问模式而不是字段数量出发设计索引；
- 能使用执行计划和 Benchmark 作为 Evidence；
- 能解释单列索引为什么不足；
- 能在读性能与写成本之间做条件化判断；
- 遇到慢查询时不会无条件先加缓存。

建议体验时长：10～15 分钟；Demo 裁剪版：约 5 分钟。

## 固定场景

表：`orders`，固定大规模 fixture。

```sql
SELECT id, user_id, status, amount, created_at
FROM orders
WHERE user_id = :user_id
ORDER BY created_at DESC
LIMIT 20;
```

稳定演示目标：

| 阶段 | 执行计划特征 | 目标耗时区间 |
|---|---|---:|
| 无索引 | Full Table Scan + Sort | 1200～2000ms |
| `user_id` 单列索引 | Index Search + Extra Sort | 180～400ms |
| `(user_id, created_at DESC)` 联合索引 | Composite Index Search | 20～60ms |

具体数值需在最终运行环境中校准；产品展示区间，不承诺固定单点数字。

## 8 Round Learning Matrix

| Round | 学习动作 | 用户界面与输入 | Evidence | 识别目标 | 下一步策略 |
|---|---|---|---|---|---|
| 1 Diagnose | Predict + Reason | 展示 SQL，询问“哪里可能慢，第一步会做什么” | 自然语言理由、方案选择 | 是否跳过定位直接缓存；是否理解查询模式 | 按回答进入 `cache_first`、`index_guess` 或 `inspect_plan` 分支 |
| 2 Observe | Run Baseline | 点击 Run，显示 Full Table Scan、约 1.8s | plan、runtime、rows scanned | 是否能把慢定位到 scan/sort | 若解释不完整，追问执行计划；不直接给答案 |
| 3 First Action | Modify | 用户创建索引或坚持缓存 | SQL diff、方案理由 | 单列索引叠加误区；缓存优先误区 | 缓存分支触发知乎 Counterpoint；索引分支进入真实运行 |
| 4 Compare | Run + Compare | 运行 `idx_user_id`，显示约 287ms | before/after runtime、plan diff | 是否注意仍有排序成本 | 提问“快了很多，为什么还没达到目标？” |
| 5 Intervention | Respond to Claim | 展示知乎观点：“索引服务真实查询模式，而不是字段数量” | 用户对 Claim 的解释或选择 | 是否把 filtering 与 ordering 联合考虑 | 生成重新设计索引任务 |
| 6 Optimize | Modify + Run | 创建 `(user_id, created_at DESC)` 联合索引并运行 | 约 31ms、plan、tests | 能否解释列顺序与排序消除 | 通过后提升 application/diagnosis，进入扰动 |
| 7 Perturb | Trade-off Decision | 新条件：每秒 5 万写入、索引维护成本增加 | 方案选择、条件说明、预估影响 | “索引越多越好”；能否权衡读写 | 根据理由要求保留、调整或删除索引，并解释条件 |
| 8 Transfer | New Query | 给出按 `status` 和时间范围的新查询，禁止照抄答案 | 新索引设计、解释、可选运行 | 是否能迁移“访问模式 → 索引”原则 | 生成结业反馈、能力变化和知乎延伸阅读 |

## 关键分支

### Branch A：缓存优先

触发条件：用户在没有查看执行计划时优先选择 Redis 或应用缓存。

系统反应：

1. 不评价“错误”；
2. 标记 `performance_cache_first` misconception candidate；
3. 引入知乎 Counterpoint：“性能优化应先定位瓶颈，而不是直接增加缓存层”；
4. 要求用户选择“坚持缓存 / 查看执行计划 / 不确定”，并解释成立条件；
5. 将后续任务导向 Round 2 Observe。

### Branch B：单列索引

触发条件：用户只在 `user_id` 上创建索引。

系统反应：真实运行并承认明显改进，但保留排序 Evidence，追问剩余瓶颈。

### Branch C：直接给出联合索引

触发条件：用户一开始就提出 `(user_id, created_at)`。

系统反应：不跳过学习；要求先预测执行计划，再真实运行，并提前进入高写入 Perturbation，验证是否只是记住答案。

## Canonical Knowledge

1. 索引服务查询访问模式，而不是孤立字段；
2. filtering、ordering、selectivity 和返回列共同影响索引设计；
3. 执行计划与 Benchmark 是判断优化是否生效的 Evidence；
4. 单列索引不能自动等价于联合索引；
5. 索引增加存储与写维护成本；
6. 缓存是架构选择，不应替代瓶颈定位。

## Misconception Catalog

| ID | 错误模型 | 识别信号 | 教学动作 |
|---|---|---|---|
| `performance_cache_first` | 慢查询首先加缓存 | 未看 plan 就选择 Redis | Counterpoint + 强制 Observe |
| `index_every_where_column` | WHERE 每列各建一个索引 | 提议多个单列索引 | 比较 plan 与排序成本 |
| `index_always_good` | 索引越多越好 | 忽略写入条件 | 高写入 Perturbation |
| `composite_equals_single` | 联合索引等于多个单列索引 | 认为优化器会自动组合 | 单列与联合索引 plan 对比 |
| `plan_index_means_fast` | plan 出现 index 就代表完成优化 | 不看耗时、排序和扫描量 | 要求多 Evidence 解释 |
| `benchmark_single_run` | 一次运行足以证明性能 | 只引用单次耗时 | warm-up + 多次测量 |
| `column_order_irrelevant` | 联合索引列顺序无关 | 无条件交换列顺序 | Transfer Query |
| `read_only_optimization` | 只考虑读取 | 忽略写放大 | 写入压力条件 |
| `select_star_free` | `SELECT *` 没有代价 | 不考虑返回列与覆盖 | 可选 covering index 讨论 |
| `memorized_best_practice` | 记住联合索引模板即可 | 无法解释条件变化 | 新查询 Transfer |

## Evidence Rubric

| 能力维度 | L0 | L1 | L2 | L3 |
|---|---|---|---|---|
| understanding | 只能复述“加索引” | 知道索引能减少扫描 | 能解释 filtering/ordering | 能形成条件化模型 |
| application | 无法修改 | 能创建单列索引 | 能创建匹配查询的联合索引 | 能迁移到新查询 |
| diagnosis | 猜测瓶颈 | 能读取 runtime | 能解释 plan 与 sort | 能组合多 Evidence 定位 |
| design | 套固定答案 | 能选候选索引 | 能解释列顺序 | 能比较多种设计 |
| tradeoff | 只追求更快 | 知道索引有成本 | 能讨论读写权衡 | 能基于负载做决策 |
| transfer | 只能完成原题 | 能处理小改动 | 能处理新过滤/排序 | 能解释未知场景边界 |

## Zhihu Intervention Dataset：首批需求

至少准备以下 Claim 类型，每条都必须有原问题、原回答、作者和 URL：

1. 慢查询应先定位瓶颈，而不是直接增加缓存层；
2. 索引设计必须基于真实查询模式；
3. 多个单列索引不等于合适的联合索引；
4. `EXPLAIN` 使用索引不等于整体查询已经足够快；
5. 高频写入表需要控制索引数量；
6. 某些场景应先改查询或分页方式；
7. 覆盖索引的收益与维护成本；
8. 生产环境 Benchmark 与本地单次测量的差异。

## Pack 完成定义

- 三个运行阶段结果稳定可复现；
- 三条关键分支可进入不同 NextAction；
- 至少一条真实知乎 Claim 改变下一步任务；
- Round 8 能区分“记住答案”和“理解原则”；
- Progress 页能解释每个能力维度为何变化；
- 失败状态、LLM fallback、知乎 Mock fallback 均可演示。
