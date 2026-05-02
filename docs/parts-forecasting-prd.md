# Parts Forecasting System — PRD

## 1. Overview

The Parts Forecasting System is a statistically driven forecasting and inventory optimisation engine designed to improve spare parts availability while minimising excess inventory.

The system integrates:
- Demand smoothing (exponential smoothing)
- Trend detection (Holt’s method)
- Outlier detection (Z-score)
- Install-driven demand modelling
- Probabilistic safety stock
- Rolling forecasting and ordering logic

The goal is to produce consistent, explainable, and risk-aware ordering decisions.

---

## 2. Problem Statement

Current ordering processes rely on:
- Historical averages
- Manual judgement
- Static rules

This results in:
- Stockouts → emergency orders, service delays
- Overstocking → excess inventory and cost
- Poor handling of installs, variability, and long lead times (~90 days)

---

## 3. Goals & Success Metrics

### Goals
- Improve forecast accuracy
- Reduce emergency orders and cannibalisation
- Maintain or improve service levels
- Provide explainable decisions

### Success Metrics
- ↑ Forecast accuracy
- ↓ Emergency orders (20–40%)
- ↓ Cannibalisation
- ≥ 90% service level
- Controlled inventory levels

---

## 4. Forecasting Engine

### Flow
1. Data preparation
2. Outlier detection
3. Demand modelling
4. Install adjustments
5. Safety stock
6. Rolling ordering

---

## 5. Usage per Machine

Usage per Machine = Total Part Usage / Total Active Machines

Used for install demand and validation.

---

## 6. Install-Driven Demand

Final Demand =
Base Forecast +
Scheduled Installs +
(Projected Installs × Confidence)

---

## 7. Rolling Forecast & Ordering

Demand_LT = Forecast × Lead Time

Reorder Point (ROP) =
Demand_LT + Safety Stock

Trigger:
projected_stock < ROP

---

## 8. MOQ Logic

required_qty = target_stock - projected_stock

if required_qty < MOQ:
    order = MOQ
else:
    order = required_qty

---

## 9. Configuration

forecasting:
  smoothing_groups:
    A: 0.7
    B: 0.4
    C: 0.2
  trend:
    beta: 0.2
  outlier_detection:
    z_threshold: 3
  service_level:
    target: 0.90
  lead_time_days: 90

---

## 10. Outputs

- Forecast demand
- Safety stock
- Reorder point
- Order quantity
- Stockout risk

---

## 11. Data Requirements

- Usage history
- Install data
- Stock levels
- Lead time
- Part-model mapping

---

## 12. Glossary

Z-Score: deviation from average  
MAE: forecast accuracy measure  
Safety Stock: buffer inventory  
ROP: reorder trigger  
Usage per Machine: parts per device

---

## 13. Principles

- Optimise decisions, not perfect predictions
- Keep explainable
- Balance service vs cost
- Rolling forecast

---

## 14. Future

- Machine learning (gradient boosting)
- Auto tuning
- 
