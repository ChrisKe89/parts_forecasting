# Small raw data fixture for Parts Forecasting

Drop the `data/raw` folder into the repo root and run:

```bash
python -m src.main
```

This fixture includes all required schema files plus optional `install_forecast.csv`. It is deliberately small but covers:

- 24 months of internal usage history
- parts mapped to multiple models
- direct and dealer fleet population
- dealer orders, direct/internal orders, partial fulfilment and backorders
- allocated stock
- open and partially received purchase orders
- scheduled and projected installs
- stable, trending, intermittent, sparse and spike usage patterns

The CSVs use the documented `part_number` schema.
