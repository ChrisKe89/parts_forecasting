# AGENTS.md — Parts Forecasting V1

## 🎯 Mission

Build a **deterministic, explainable forecasting prototype** that:

- Predicts spare parts demand for the **post–lead-time window**
- Simulates real-world ordering decisions
- Backtests forecasts against actual demand
- Demonstrates improvement over current manual ordering

---

## 🧠 Core Model Principle (DO NOT VIOLATE)

This system does NOT forecast the next 90 days.

It forecasts:

Demand occurring AFTER lead time.

Forecast Window = [T + 90 days → T + 180 days]

Where:
- T = forecast decision date

---

## ⚠️ Hard Constraints

The agent MUST:

- ❌ NOT use machine learning
- ❌ NOT introduce probabilistic models
- ❌ NOT use external APIs
- ❌ NOT add databases
- ❌ NOT introduce dashboards
- ❌ NOT change data schema without instruction
- ❌ NOT use future data (no leakage)

The agent MUST:

- ✅ keep logic deterministic and explainable
- ✅ use only CSV-based data
- ✅ follow the defined folder structure
- ✅ implement lead-time-aware backtesting exactly

---

## 📁 Project Structure (STRICT)

parts-forecasting-v1/

├── data/ │   ├── raw/ │   ├── processed/ │   └── output/ │ ├── src/ │   ├── config.py │   ├── load_data.py │   ├── prepare_data.py │   ├── feature_engineering.py │   ├── forecast.py │   ├── ordering.py │   ├── backtest.py │   └── main.py │ └── README.md

Do not restructure without explicit instruction.

---

## 📦 Required Input Schema

### Usage Data

part_number model date qty

### Install Data

model date qty

### Emergency Orders

part_number date qty

### Cannibalised Parts

part_number date qty

### Stock Snapshot (Optional)

part_number stock_on_hand stock_on_order snapshot_date

### Part ↔ Model Mapping

part_number model

---

## 🧱 Data Rules

- Dates must be parsed as datetime
- All aggregation must support monthly grouping
- Part numbers and models must be uppercase
- Null keys must be removed
- Quantity must be numeric

---

## 🧠 Feature Engineering Rules

At forecast time T:

### Recent Usage Trend

avg usage over last 3 months × 3

### Usage Rate

total usage (training window) / average installed base (training window)

### Installed Base Demand

installed_base_at_T × usage_rate_90

### Growth Adjustment

installs_last_3_months × usage_rate_90

---

## 🔮 Forecast Formula (FIXED)

predicted_demand = recent_usage_trend

installed_base_demand

growth_adjustment


Do not alter this formula.

---

## 📦 Ordering Logic

recommended_order = predicted_demand

safety_buffer


stock_on_hand

stock_on_order


Rules:

- negative → 0
- round up
- minimum order = 1 if demand > 0

---

## 🔁 Backtesting (CRITICAL)

### Windows Definition

At forecast date T:

Training Window: [T - 9 months → T]

Lead-Time Gap: [T → T + 90 days]

Evaluation Window: [T + 90 → T + 180 days]

### Strict Rules

- Do NOT use data from lead-time gap
- Do NOT use data from evaluation window
- Only compare forecast vs actual in evaluation window

---

## 📊 True Demand Definition

true_demand = usage

emergency_orders

cannibalised_parts


Calculated ONLY inside evaluation window.

---

## 🔁 Rolling Backtest

Agent MUST implement:

for each valid forecast date T: train on past 9 months forecast future window compute actual demand store result

Must support ~10+ forecast runs using 24 months data.

---

## 📤 Output Requirements

Each row must contain:

forecast_date part_number model

training_start training_end

lead_time_start lead_time_end

evaluation_start evaluation_end

predicted_demand true_demand

recommended_order safety_buffer

forecast_error absolute_error

under_forecast_qty over_forecast_qty

---

## 🧪 Execution Order (MANDATORY)

1. Implement data loading
2. Implement data cleaning
3. Implement monthly aggregation
4. Implement installed base calculation
5. Implement single forecast point (hardcoded T)
6. Implement true demand calculation
7. Implement forecast vs actual comparison
8. Implement rolling backtest loop
9. Implement CSV output
10. Implement summary metrics

Agent must NOT skip steps.

---

## 🧭 Development Rules

- One logical change per commit
- Do not mix refactoring with feature work
- Preserve behaviour unless explicitly changing logic
- Stop if uncertainty impacts correctness of model

---

## 🚫 Known Failure Modes (Avoid These)

The agent must NOT:

- compare forecast to immediate next 90 days
- include lead-time gap in evaluation
- mix training and evaluation data
- assume stock history exists
- over-engineer the solution

---

## 🎯 Definition of Done (V1)

The system is complete when:

- Forecasts are generated for all parts
- Rolling backtest runs successfully
- Forecast vs actual is calculated correctly
- Output CSV is produced
- No future data leakage occurs
- Results are explainable

---

## 💡 Guiding Principle

This is NOT a perfect forecasting system.

This is a **proof that structured logic improves ordering decisions**.

Keep it simple.
Keep it correct.
Do not overbuild.


---
