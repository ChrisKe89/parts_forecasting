# Architecture

Flow: data load/validation -> outlier detection and usage adjustment -> usage per machine -> base forecast (exp smoothing or Holt when trend significant) -> install-adjusted demand -> safety stock -> lead-time demand -> reorder point -> MOQ-constrained order recommendation -> backtesting.
