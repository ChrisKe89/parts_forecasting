# PRD Alignment Audit

| PRD section | Current repo support | Missing gaps | Implementation status | Files affected |
|---|---|---|---|---|
| Data prep / outlier / smoothing | Existing support for z-score, smoothing, holt | Trend significance notes and explicit explainability | Completed in this change | `src/forecasting/engine.py`, `src/forecasting/calculations.py` |
| Lead-time demand | Previously implicit monthly scaling | Explicit weekly demand rate, window start/end, lead-time demand outputs | Completed | `src/inventory/logic.py`, `src/forecasting/engine.py` |
| Safety stock | Formula existed but fixed z and monthly approximation | Service-level-derived z-score and sparse-history fallback | Completed | `src/forecasting/calculations.py`, `src/forecasting/engine.py` |
| Reorder point logic | Basic ROP and trigger existed | Explicit reason and projected stock at arrival | Completed | `src/forecasting/engine.py`, `src/inventory/logic.py` |
| MOQ logic | Simple max(required, MOQ) | Non-trigger -> zero order and MOQ adjustment flag | Completed | `src/inventory/logic.py`, `src/forecasting/engine.py` |
| Rolling weekly simulation | Limited projected stock estimate | Weekly cadence, arrival date, stockout risk before arrival, incoming orders | Completed | `src/inventory/logic.py`, `src/forecasting/engine.py` |
| Install-driven adjustment | Present | Availability flag and confidence factor output | Completed | `src/forecasting/engine.py` |
| Explainability | Minimal fields | Human-readable recommendation explanation | Completed | `src/forecasting/engine.py` |
| Tests | Baseline tests | PRD-specific deterministic tests for inventory + install logic | Completed | `tests/test_system.py` |
| Test data | Synthetic generator existed | Explicit deterministic test-data folder usage documentation | Completed | `data/test_data/*.csv`, `docs/data_dictionary.md` |

## Behavior Changes

- Output schema uses part-level decision rows and includes stock traceability fields (`stock_on_hand_qty`, `allocated_qty`, `backorder_qty`, `effective_stock_qty`, `pipeline_supply_qty`) plus deterministic `recommendation_explanation`. Model-level calculations remain supporting inputs and are aggregated before reorder logic.
