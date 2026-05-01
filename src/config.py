"""Configuration for lead-time-aware parts forecasting."""

from pathlib import Path

LEAD_TIME_DAYS = 90
EVALUATION_WINDOW_DAYS = 90
TRAINING_WINDOW_MONTHS = 9

SAFETY_BUFFER_PERCENT = 0.25
MINIMUM_ORDER_QTY = 1

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
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
