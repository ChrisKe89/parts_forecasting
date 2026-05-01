from pathlib import Path

LEAD_TIME_DAYS = 90
EVALUATION_WINDOW_DAYS = 90

BACKTEST_TRAINING_WINDOW_MONTHS = 9
PRODUCTION_TRAINING_WINDOW_MONTHS = 12
DEFAULT_FORECAST_HORIZON_MONTHS = 3

MINIMUM_ORDER_QTY = 1
BASE_BUFFER_PCT = 0.25
VARIABILITY_BUFFER_MULTIPLIER = 0.25
MAX_VARIABILITY_BUFFER_PCT = 0.75

SPARSE_USAGE_THRESHOLD = 3
SPARSE_DAMPING_FACTOR = 0.5
VOLATILITY_CV_THRESHOLD = 1.5
VOLATILITY_DAMPING_FACTOR = 0.75

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DATA_DIR = DATA_DIR / "output"

INPUT_FILES = {
    "usage": RAW_DATA_DIR / "usage_data.csv",
    "installs": RAW_DATA_DIR / "install_data.csv",
    "emergency": RAW_DATA_DIR / "emergency_orders.csv",
    "cannibalised": RAW_DATA_DIR / "cannibalised_parts.csv",
    "stock": RAW_DATA_DIR / "stock_snapshot.csv",
    "mapping": RAW_DATA_DIR / "part_model_mapping.csv",
}

OUTPUT_FILE = OUTPUT_DATA_DIR / "forecast_backtest_results.csv"
SUMMARY_FILE = OUTPUT_DATA_DIR / "forecast_backtest_summary.csv"
