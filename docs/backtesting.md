# Backtesting

Backtesting uses deterministic date slicing with configurable train/test windows.

Default runtime window:
- 18 month train
- 6 month test

Metrics:
- MAE = mean(|forecast - actual|)
- RMSE = sqrt(mean((forecast - actual)^2))
- Bias = mean(forecast - actual)
- Under/over forecast counts
- Service level estimate = fraction where forecast >= actual
- Stockout count from projected stock at arrival < 0
