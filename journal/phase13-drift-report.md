# Phase 13 Drift Monitoring Report

**Generated:** 2026-04-24 | **Checks:** 14

## Severity Summary

| Status | Count |
|--------|------:|
| ✅ OK | 13 |
| ⚠️ WARNING | 0 |
| 🔔 ALERT | 1 |
| 🚨 CRITICAL | 0 |

## Check Results

| Check | Layer | Type | Severity | Action |
|-------|-------|------|----------|--------|
| `xgboost_feature_drift` | Layer 1 | feature_drift | ok | retrain |
| `xgboost_performance_drift` | Layer 1 | performance_drift | ok | retrain |
| `xgboost_prediction_bias` | Layer 1 | concept_drift | ok | retrain |
| `efficientnet_confidence_drift` | Layer 1b | performance_drift | ok | retrain |
| `efficientnet_diagnosis_rate` | Layer 1b | feature_drift | alert | alert_manager |
| `milp_infeasibility_rate` | Layer 2 | performance_drift | ok | alert_manager |
| `milp_solve_time_drift` | Layer 2 | performance_drift | ok | alert_manager |
| `milp_constraint_violations` | Layer 2 | concept_drift | ok | review_immediately |
| `ppo_reward_drift` | Layer 3 | performance_drift | ok | retrain |
| `ppo_action_distribution_drift` | Layer 3 | concept_drift | ok | retrain |
| `segment_stability` | Layer 4 | concept_drift | ok | recluster |
| `customer_segment_size_drift` | Layer 4 | feature_drift | ok | recluster |
| `rag_relevance_drift` | Layer 5 | performance_drift | ok | knowledge_base_review |
| `data_freshness` | System-wide | feature_drift | ok | alert_immediately |