# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog and this project uses Semantic Versioning.

## [Unreleased]

### Added

- Added PRD-aligned forecast trace fields for base demand, dealer demand, install adjustment, forecast method, trend, outlier count, effective stock, pipeline supply, and projected stock.
- Added regression tests covering dealer/direct demand separation, install weighting, inventory position calculations, and Holt trend gating.

### Changed

- Forecasting now uses configured smoothing groups, applies Holt's method only after documented history and trend gates pass, and calculates safety stock from observed demand variability and service-level target.
- Loader now passes dealer orders into forecasting, maps model-only install forecasts to compatible parts, and limits backorder quantities to dealer demand.
