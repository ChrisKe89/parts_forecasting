from pathlib import Path
from data.loader import load_inputs
from forecasting.engine import run_forecast
from backtesting import run_backtest
from data.synthetic_generator import generate_synthetic_data


def main() -> None:
    synthetic_dir = Path("data/synthetic")
    generate_synthetic_data(synthetic_dir)
    data = load_inputs(synthetic_dir)
    output = run_forecast(data)
    output.to_csv("data/output/forecast_output.csv", index=False)
    backtest = run_backtest(data)
    backtest.to_csv("data/output/backtest_output.csv", index=False)


if __name__ == "__main__":
    main()
