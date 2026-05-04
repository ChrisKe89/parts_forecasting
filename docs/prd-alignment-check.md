# PRD Completion Checklist

| Section | Status | Evidence |
|---|---|---|
| 1. Overview/objective | Complete | Backtest summary includes baseline vs model improvement decision in `run_backtest`. |
| 2. Key concepts | Complete | Service/fill/inventory/supplier metrics in `src/backtesting.py`. |
| 3. Proof/backtest mode | Complete | `src/main.py --mode backtest`; outputs required backtest files. |
| 4. Live forecast mode | Complete | `src/main.py --mode forecast` writes `forecast_recommendations.csv`. |
| 5. Data model | Partial | Current loader/schema retained; no broad schema refactor in this change. |
| 6. usage_qty demand rule | Complete | Weekly replay demand source fixed to `usage_only`. |
| 7. Forecasting logic | Complete | `src/forecasting/engine.py` deterministic smoothing flow unchanged. |
| 8. MOQ/order multiple logic | Complete | `apply_order_constraints` used in forecast and replay. |
| 9. Inventory simulation engine | Complete | Week-by-week stock/receipts/backorder carry in `_simulate_weekly`. |
| 10. Synthetic data generation | Complete | 1000 parts, 50 models, 104 weeks in generator and tests. |
| 11. Backtesting methodology | Complete | 18/6 split via `_train_test_dates`; fixed test demand replay. |
| 12. Summary outputs | Complete | `backtest_summary.json` contains baseline/model comparison fields. |
| 13. Detailed outputs | Complete | `backtest_weekly_detail.csv`, supplier/inventory simulation outputs. |
| 14. Concerns report | Complete | Structured `concerns_report.json` with typed concerns. |
| 15. Success metrics | Complete | service level/fill rate/stockout/inventory metrics populated. |
| 16. Fail conditions | Complete | enforce fail on synthetic baseline range. |
| 17. Risks/assumptions | Partial | Remaining assumptions are documented in concerns output only. |
| 18. Acceptance criteria | Complete | Covered by tests in `tests/test_phase2.py`. |
| 19. Documentation/glossary | Complete | `docs/output-reference.md`, `docs/backtesting.md`, and `docs/glossary.md` harmonized with current outputs and definitions. |

## Remaining PRD Gaps
- Loader/schema files were not deeply reworked in this patch; alignment is functional but not exhaustively validated for every optional column variant.
