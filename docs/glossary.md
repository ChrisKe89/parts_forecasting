# Glossary

Each term includes description, formula, example, interpretation, where used.

- **Exponential smoothing**: weighted forecasting favoring recent demand. Formula: `L_t = alpha*Y_t + (1-alpha)*L_(t-1)`. Example: alpha 0.7 responds faster. Used in base forecast.
- **Alpha**: smoothing weight by group (A=0.7, B=0.4, C=0.2).
- **Holt's method**: level + trend smoothing. Formula uses alpha and beta updates for level/trend.
- **Beta**: trend smoothing factor in Holt.
- **Trend**: slope in Holt output; positive up, negative down.
- **Z-score**: `(x-mean)/std_dev`; flags outliers.
- **Mean**: arithmetic average usage.
- **Standard deviation**: demand variability magnitude.
- **Outlier**: point with `|z| > threshold`.
- **Usage per machine**: `total_part_usage/total_active_machines`.
- **Scheduled installs**: future installs included at 100%.
- **Projected installs**: future installs weighted by confidence.
- **Projected install confidence**: probability multiplier [0,1].
- **Safety stock**: probabilistic inventory buffer.
- **Service level**: target fill probability (default 0.90).
- **Stockout risk**: high when projected stock < reorder point.
- **Demand during lead time**: `forecast * lead_time_days/30`.
- **Reorder point**: `demand_during_lead_time + safety_stock`.
- **MOQ**: minimum order quantity applied after trigger.
- **MAE**: mean absolute error.
- **Forecast error**: forecast - actual.
- **Rolling forecast**: repeated weekly projection.
