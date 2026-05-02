📄 1. PRD (updated – authoritative)

Use this as your docs/parts-forecasting-prd.md


---

Parts Forecasting & Inventory Recommendation System

Objective

Provide a deterministic, explainable system to:

Forecast spare part demand

Calculate inventory requirements

Recommend order quantities

Minimise stockouts and excess stock



---

Core Principles

- Forecasting is performed at part level
- Model-level data is used only where it adds value
- Internal usage is the most reliable demand signal
- Dealer demand is part-level only and treated separately
- All calculations must be explainable (no black box logic)


---

Data Sources

Demand Signals

Source	Description	Confidence

Internal usage	Technician/service usage	High
Dealer orders	External demand	Medium
Install forecast	Future demand	High (scheduled) / Medium (projected)



---

Supply Signals

Source	Description

Stock snapshot	Current inventory
Open purchase orders	Inbound supply
Allocations	Reserved stock
Backorders	Unfulfilled demand



---

Forecasting Flow

Internal usage
→ Clean & detect outliers
→ Calculate usage per machine
→ Aggregate to part-level demand
→ Apply smoothing / Holt trend
→ Add dealer demand
→ Add install demand
→ Final demand forecast


---

Inventory Logic

Effective Stock =
stock_on_hand
- allocated_qty
- backorder_qty

Projected Stock =
effective_stock
+ inbound_orders_before_arrival
- demand_before_arrival

Reorder Point =
lead_time_demand + safety_stock

Order Decision:
IF projected_stock < reorder_point:
    order_qty = max(required_qty, MOQ)
ELSE:
    order_qty = 0


---

Key Outputs

Forecast demand (weekly)
Safety stock
Lead-time demand
Reorder point (ROP)
Projected stock at arrival
Recommended order quantity
Stockout risk


---

Known Limitations

Dealer demand is not model-specific
Backtesting uses simplified time scaling (not full simulation yet)
Forecast accuracy depends on usage data quality


---

📄 2. DATA SCHEMA DOCUMENT

Create: docs/data-schema.md


---

Overview

All input data must conform to defined schemas.
Validation is strict for required fields and permissive (warn-only) for optional enhancements.


---

Table Summary

File	Purpose

parts_master.csv	Part definitions
part_model_mapping.csv	Part ↔ model relationships
internal_parts_usage.csv	Internal demand
orders.csv	Dealer demand + fulfilment
stock_snapshot.csv	Current stock
open_purchase_orders.csv	Inbound stock
active_machine_population.csv	Fleet size
install_forecast.csv	Future installs (optional)



---

Naming Rules

All fields must be dataset-specific:

✔ usage_date
✔ order_qty
✔ install_date

✘ date
✘ qty


---

Critical Design Rules

- Parts can map to multiple models
- Dealer demand does not require model mapping
- Internal usage must match part-model mapping
- Forecasting happens at part level


---

📄 3. GLOSSARY (this is important for adoption)

Create: docs/glossary.md


---

Demand Terms

Usage per Machine

usage_per_machine =
total_usage / active_machine_qty


---

Base Forecast

Forecast derived from historical usage using smoothing or Holt trend


---

Install Demand

Demand generated from new machine installs


---

Inventory Terms

Safety Stock

safety_stock =
Z × std_dev × √lead_time


---

Lead Time Demand

lead_time_demand =
weekly_demand × lead_time_weeks


---

Reorder Point (ROP)

ROP = lead_time_demand + safety_stock


---

MOQ (Minimum Order Quantity)

Minimum quantity supplier allows per order


---

Backorder

Unfulfilled demand from customer orders


---

Allocated Stock

Stock reserved for orders but not yet fulfilled


---

Pipeline Supply

Open purchase orders expected to arrive


---

Projected Stock

Future stock level after demand and supply


---

Forecast Metrics

MAE

Mean Absolute Error

RMSE

Root Mean Squared Error

Forecast Bias

Average over/under forecast


---

📄 4. ARCHITECTURE DOC

Create: docs/architecture.md


---

System Flow

CSV Input
→ Schema Validation
→ Data Preparation
→ Forecast Engine
→ Inventory Engine
→ Backtesting Engine
→ Output CSVs


---

Module Responsibilities

data/ → load + validate
forecasting/ → demand logic
inventory/ → stock + ordering logic
backtesting/ → evaluation
utils/ → config + helpers


---

Design Constraints

- No ML
- Fully deterministic
- Fully explainable
- Config-driven behaviour


---

📄 5. OUTPUT REFERENCE

Create: docs/output-reference.md


---

Forecast Output Fields

Column	Description

base_forecast	Smoothed demand
final_adjusted_demand	Demand including installs
safety_stock	Buffer stock
reorder_point	ROP
projected_stock	Stock at arrival
final_order_quantity	Recommended order



---

Key Flags

reorder_triggered → whether order is needed
moq_adjustment_applied → MOQ enforced
stockout_risk_before_arrival → negative projected stock


---

📄 6. VALIDATION RULES DOC

Create: docs/data-validation.md


---

Error vs Warning

Errors (fail run)

Missing required file
Missing required column
Invalid data type
Negative quantities
Invalid relationships


---

Warnings (continue run)

Unknown model
Install data missing
Outliers detected
Inconsistent optional fields


---

📄 7. README (top-level)

Update to:

What this is
How to run
Where to put data
What outputs are created

No mention of:

prototype
V1
future phase


---
