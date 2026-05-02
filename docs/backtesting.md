# Backtesting

Supported windows:
- 21 month train + 3 month test
- 9 month train + 3 month test

Metrics:
- MAE = mean(|forecast - actual|)
- RMSE = sqrt(mean((forecast - actual)^2))
- Bias = mean(forecast - actual)
- Under/over forecast counts
- Service level estimate = fraction where forecast >= actual
- Stockout count from projected stock at arrival < 0
