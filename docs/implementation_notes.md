# Implementation Notes

## Commands

- Install deps: `pip install -r requirements.txt`
- Generate synthetic data: `python -m src.main`
- Run forecast: `python -m src.main`
- Run tests: `pytest`
- Run backtests: `python -m src.main` (writes `data/output/backtest_output.csv`)

## Determinism

Synthetic generator uses fixed seed (`42`) by default.
All methods are statistical and deterministic.
