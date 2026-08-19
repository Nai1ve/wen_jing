# 核心数据契约草案

状态：`draft-0.1`。用于前端 fixture、后端实现和 LLM schema 对齐；技术栈确定后再转成正式 JSON Schema / TypeScript / Pydantic 定义。

## 1. LearningSession

```json
{
  "id": "session_001",
  "pack_id": "database_index_v1",
  "user_id": "demo_user",
  "status": "active",
  "current_round": 4,
  "learner_state": {
    "concepts": {}
  },
  "history": [],
  "created_at": "2026-08-19T00:00:00Z",
  "updated_at": "2026-08-19T00:05:00Z"
}
```

约束：`status` ∈ `created | active | completed | abandoned`；服务端拥有 `current_round` 的最终解释权。

## 2. Attempt

```json
{
  "id": "attempt_004",
  "session_id": "session_001",
  "round_id": "round_04_compare",
  "action_type": "run_sql",
  "input": {
    "sql": "CREATE INDEX idx_user_id ON orders(user_id);",
    "reasoning": "先减少 user_id 的扫描范围"
  },
  "client_context": {
    "selected_option": "single_column_index"
  },
  "submitted_at": "2026-08-19T00:04:30Z"
}
```

约束：原始用户输入不可被 LLM 改写后覆盖；如需规范化，另存字段。

## 3. Evidence

```json
{
  "id": "evidence_004",
  "attempt_id": "attempt_004",
  "kind": "sql_execution",
  "observations": {
    "runtime_ms": 287,
    "runtime_samples_ms": [281, 287, 294],
    "plan": ["SEARCH orders USING INDEX idx_user_id", "USE TEMP B-TREE FOR ORDER BY"],
    "rows_returned": 20,
    "tests": [
      {"name": "result_correctness", "passed": true}
    ]
  },
  "provenance": {
    "producer": "sqlite_runner",
    "fixture_version": "orders_v1",
    "runner_version": "0.1.0"
  },
  "captured_at": "2026-08-19T00:04:31Z"
}
```

约束：客观 Runner Evidence 与 LLM 评价分离；LLM 不得生成或修改 runtime、plan、tests。

## 4. ConceptState

```json
{
  "concept_id": "composite_index",
  "dimensions": {
    "understanding": 2,
    "application": 1,
    "diagnosis": 2,
    "design": 1,
    "tradeoff": 0,
    "transfer": 0
  },
  "confidence": "medium",
  "supporting_evidence_ids": ["evidence_002", "evidence_004"],
  "active_misconceptions": ["composite_equals_single"],
  "last_updated_by": "learning_engine"
}
```

约束：竞赛版维度取值为 0～3；每次更新必须引用 Evidence 或用户 reasoning，不允许无依据升级。

## 5. KnowledgeIntervention

```json
{
  "id": "intervention_001",
  "type": "counterpoint",
  "trigger": {
    "round_id": "round_03_first_action",
    "misconception_id": "performance_cache_first",
    "evidence_ids": ["evidence_001"]
  },
  "concept_id": "query_optimization",
  "claim": "性能优化应先定位瓶颈，而不是直接增加缓存层。",
  "reason": "缓存会增加一致性和失效复杂度，且不能修复低效访问路径本身。",
  "scenario": "慢 SQL 尚未检查执行计划",
  "counterpoint": "当热点数据稳定、允许一定陈旧且数据库已优化时，缓存仍可能合适。",
  "prompt_to_user": "这个观点成立的前提是什么？你要坚持缓存，还是先检查执行计划？",
  "source": {
    "provider": "zhihu",
    "question_id": "pending",
    "answer_id": "pending",
    "title": "pending",
    "author": "pending",
    "url": "pending"
  }
}
```

约束：`type` ∈ `claim | counterpoint | case | caution | question`；`source.url` 在真实 Provider 中必填；生成内容必须与原回答区分。

## 6. NextLearningAction

```json
{
  "id": "action_005",
  "type": "explain_plan",
  "round_id": "round_04_compare",
  "instruction": "单列索引已经让查询快了很多。请根据新的执行计划解释剩余成本。",
  "inputs": {
    "visible_evidence_ids": ["evidence_004"],
    "starter_code": null,
    "options": []
  },
  "completion": {
    "required_evidence_kinds": ["user_reasoning"],
    "rubric_id": "rubric_remaining_sort_cost"
  },
  "fallback": {
    "type": "multiple_choice",
    "options": ["仍在排序", "仍是全表扫描", "网络延迟", "无法判断"]
  }
}
```

约束：`NextLearningAction` 是 Learning Engine 的唯一前端导航决策，不允许 LLM 直接返回任意页面路由。

## 7. Learning Engine 输入输出

输入：

```json
{
  "session": {},
  "current_action": {},
  "attempt": {},
  "evidence": [],
  "available_interventions": []
}
```

结构化输出：

```json
{
  "diagnosis": {
    "summary": "用户能识别过滤条件，但尚未考虑 ORDER BY",
    "misconception_candidates": ["composite_equals_single"],
    "confidence": "high"
  },
  "feedback": {
    "acknowledgement": "单列索引显著减少了扫描范围。",
    "question": "执行计划里还有哪一步没有被索引消除？"
  },
  "state_updates": [
    {
      "concept_id": "single_column_index",
      "dimension": "application",
      "from": 0,
      "to": 1,
      "evidence_ids": ["evidence_004"]
    }
  ],
  "selected_intervention_id": null,
  "next_action": {}
}
```

## 8. Provider 内部协议

```json
{
  "query": "MySQL 慢查询 缓存 索引",
  "results": [
    {
      "provider": "zhihu",
      "question_id": "...",
      "answer_id": "...",
      "title": "...",
      "author": "...",
      "excerpt": "...",
      "url": "...",
      "published_at": "...",
      "metrics": {}
    }
  ]
}
```

`MockZhihuProvider` 与 `ZhihuProvider` 必须返回同一结构。任何 Access Secret、OAuth token 和原始敏感响应都不得进入前端 fixture、日志或 LLM prompt。

## 9. 契约冻结前检查

- 所有 enum 有明确 fallback；
- 所有时间为 ISO 8601，Runner timestamp 另行记录；
- 所有状态升级有 Evidence 引用；
- 所有真实知乎内容有 provenance；
- 用户输入、Runner 事实、LLM 推断三者字段分离；
- Mock 与真实 Provider 可互换；
- 前端只依赖内部契约，不依赖知乎原始 schema；
- LLM 输出通过 schema 校验，失败进入固定动作而不是中断会话。
