# Parts Forecasting System — Agent Execution Guide

## 1. Purpose

This document defines how AI agents (e.g. Codex) must operate when working on the Parts Forecasting System.

Objectives:

- Maintain correctness and stability
- Enforce PRD alignment
- Ensure deterministic, explainable outputs
- Prevent uncontrolled changes

## 2. Source of Truth

Authoritative documents:

- `/docs/parts-forecasting-prd.md`
- `/docs/data-schema.md`
- `/docs/glossary.md`
- `/docs/data-validation.md`

Rule:

> If any conflict exists, the PRD takes precedence.

Agents MUST NOT invent new behaviour outside these documents.

## 3. Core System Constraints (NON-NEGOTIABLE)

Agents MUST:

- Preserve existing behaviour unless explicitly instructed
- Keep all logic deterministic (same input → same output)
- Ensure all calculations are explainable and traceable
- Align all outputs with documented schema

Agents MUST NOT:

- Introduce machine learning or statistical black-box models
- Change calculation definitions
- Rename or repurpose schema fields
- Introduce hidden state, caching side-effects, or implicit behaviour
- Add undocumented assumptions

## 4. Data Contract (CRITICAL)

The system is schema-driven.

Agents MUST:

- Validate all input data before processing
- Fail on schema errors
- Continue on warnings with reporting
- Never infer missing required data

Strict rules:

- All column names must match `docs/data-schema.md`
- No generic names (e.g. `date`, `qty`)
- No silent coercion of invalid data

## 5. Architecture

The system is structured as:

- `/src/data` — load + validate
- `/src/forecasting` — demand modelling
- `/src/inventory` — stock + ordering logic
- `/src/utils` — config + helpers
- `/tests`
- `/docs`

Agents MUST NOT introduce parallel or duplicate architectures.

## 6. Forecasting Rules

Agents MUST implement exactly:

### 6.1 Demand Inputs

- Internal usage → primary signal
- Dealer orders → part-level demand only
- Install forecast → model-driven adjustment

### 6.2 Outlier Handling

- Z-score based
- Config-driven threshold
- Must preserve original values for explainability

### 6.3 Forecast Methods

- Exponential smoothing (default)
- Holt’s method ONLY if:
  - sufficient history exists
  - trend significance threshold is met

### 6.4 Usage per Machine

- Derived from internal usage + active population
- Must be model-aligned

### 6.5 Install Demand

- Scheduled = 100%
- Projected = weighted by confidence

## 7. Inventory Rules

Agents MUST implement exactly:

### 7.1 Stock Position

`effective_stock = stock_on_hand - allocated_qty - backorder_qty`

### 7.2 Pipeline Supply

`pipeline_supply = sum(open_purchase_orders arriving before target date)`

### 7.3 Demand

`final_demand = forecast_demand + install_adjustment`

### 7.4 Reorder Logic

`ROP = lead_time_demand + safety_stock`

If projected stock is below ROP, trigger order; otherwise no order.

### 7.5 MOQ

- Applied AFTER order quantity is calculated
- Must not affect reorder trigger

## 8. Orders & Demand Separation

Agents MUST enforce:

- `internal_parts_usage.csv` = internal demand (model-aware)
- `orders.csv`:
  - dealer orders = demand
  - direct/tech orders = NOT demand (if already captured in usage)
- `open_purchase_orders.csv` = supply (NOT demand)

Mixing these is a critical failure.

## 9. Validation Requirements

Agents MUST implement:

### Errors (fail execution)

- Missing required files
- Missing required columns
- Invalid data types
- Invalid relationships
- Negative quantities (unless explicitly allowed)

### Warnings (continue)

- Unknown models
- Missing optional data
- Outliers
- Partial inconsistencies

All issues must be written to:

`schema_validation_report.csv`

## 10. Testing Requirements

Agents MUST:

- Add tests for all calculations
- Maintain deterministic outputs
- Ensure full test suite passes

Required coverage:

- Z-score logic
- Smoothing
- Trend gating
- Install adjustments
- Stock calculations
- Reorder logic
- MOQ handling
- Backtest metrics

## 11. Backtesting

Agents MUST support:

- Configurable train/test windows
- Forecast vs actual comparison

Metrics required:

- MAE
- RMSE
- Bias
- Under/over forecast counts
- Service level estimate
- Stockout count

## 12. Logging & Traceability

Agents MUST:

- Allow part-level traceability
- Expose intermediate values where needed
- Keep outputs explainable

Agents MUST NOT introduce noisy or excessive logging.

## 13. Change Control

Agents MUST:

- Make small, isolated changes
- Avoid broad refactors unless instructed
- Keep commits logically scoped

## 14. Stop Conditions

Agents MUST STOP immediately if:

- PRD or schema is unclear
- A change alters calculation meaning
- Required data assumptions are missing
- Behaviour would change unintentionally

## 15. Out of Scope (STRICT)

Agents MUST NOT implement:

- Machine learning models
- Predictive AI systems
- Auto-tuning algorithms
- Heuristic optimisation layers

## 16. Final Rule

If uncertain:

> Do not guess. Follow the PRD or stop.
