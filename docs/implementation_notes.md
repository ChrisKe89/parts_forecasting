# Implementation Notes

- Forecasting and inventory outputs are contract-driven by `docs/parts-forecasting-prd.md` and `docs/data-schema.md`.
- Input CSV validation behavior is defined in `docs/data-validation.md`.
- Documentation now reflects production-style data contracts; follow-up code alignment tasks may still be required where runtime loaders use legacy field names.


## Runtime workflow
Normal runtime uses `python -m src.main` against real raw CSV files in `data/raw`. Synthetic generation remains available only via explicit utility invocation (`python -m src.data.synthetic_generator`).
