Parts Forecasting System — Agent Execution Guide

---

1. Purpose

This document defines how AI agents (e.g. Codex) must operate when working on the Parts Forecasting System.

The goal is to ensure:

- Safe, incremental development
- No unintended behaviour changes
- Full alignment with the PRD
- Reproducible and testable outputs

---

2. Source of Truth

The following documents are authoritative:

- "/docs/parts-forecasting-prd.md"
- "/docs/glossary.md"
- "/docs/data_dictionary.md"

If a conflict exists:

«PRD takes precedence over all implementation decisions.»

---

3. System Principles (DO NOT VIOLATE)

Agents MUST:

- Preserve existing behaviour unless explicitly instructed
- Keep all calculations explainable
- Avoid introducing black-box logic
- Maintain deterministic outputs (same input → same output)
- Keep all transformations traceable

Agents MUST NOT:

- Introduce machine learning models
- Change calculation definitions
- Modify column meanings or formats
- Introduce hidden state or side effects
- Optimise prematurely

---

4. Architecture Overview

The system is composed of the following layers:

4.1 Data Layer

- Raw input ingestion
- Data validation
- Schema enforcement

4.2 Processing Layer

- Outlier detection (Z-score)
- Usage per machine calculation
- Demand modelling:
  - Exponential smoothing
  - Holt’s method (conditional)
- Install-driven demand adjustment

4.3 Inventory Logic Layer

- Lead time demand calculation
- Safety stock calculation
- Reorder point calculation
- MOQ handling

4.4 Output Layer

- Forecast outputs
- Risk metrics
- Order recommendations

---

5. File & Module Structure

Agents should organise code as follows:

/src
  /data
  /forecasting
  /inventory
  /utils
/tests
/docs

---

6. Implementation Rules

6.1 One Responsibility per Module

Each file must have a single clear purpose.

---

6.2 No Hidden Logic

All calculations must:

- Be explicitly defined in code
- Match PRD definitions
- Be easy to trace

---

6.3 Naming Conventions

Use clear, explicit names:

GOOD:

- "usage_per_machine"
- "reorder_point"
- "safety_stock"

BAD:

- "calc1"
- "temp_val"
- "x"

---

6.4 No Magic Numbers

All constants must come from config:

forecasting:
  smoothing_groups:
    A: 0.7

---

7. Forecasting Logic Requirements

Agents MUST implement:

7.1 Outlier Detection

- Z-score calculation
- Configurable threshold
- Exclusion or flagging based on config

---

7.2 Usage per Machine

- Calculated per part + model
- Aligned time window

---

7.3 Exponential Smoothing

- Group-based (A/B/C)
- Config-driven alpha values

---

7.4 Holt’s Method

- Only applied when:
  - sufficient history exists
  - trend is significant

---

7.5 Install Adjustments

- Scheduled installs = 100% included
- Projected installs = weighted by confidence

---

8. Inventory Logic Requirements

Agents MUST implement:

8.1 Lead Time Demand

- Based on forecast × lead time

---

8.2 Reorder Point (ROP)

- ROP = demand during lead time + safety stock

---

8.3 Order Trigger

if projected_stock < reorder_point:
    trigger order

---

8.4 MOQ Handling

- Applied AFTER order quantity is calculated
- Must not affect reorder trigger

---

9. Testing Requirements

Agents MUST:

- Add unit tests for every calculation
- Validate against known examples
- Ensure deterministic outputs

Test categories:

- Z-score correctness
- Smoothing accuracy
- Trend detection
- Install adjustments
- Inventory logic

---

10. Backtesting Requirements

Agents MUST support:

- Training window (e.g. 9 months)
- Testing window (e.g. 3 months)
- Comparison of forecast vs actual

Metrics to include:

- MAE
- Forecast error distribution

---

11. Logging & Debugging

Agents MUST:

- Log intermediate calculations
- Allow traceability per part
- Provide debug output for:
  - forecast components
  - install adjustments
  - inventory decisions

---

12. Change Management

Agents MUST:

- Make small, incremental changes
- Use one commit per logical change
- Avoid large refactors without instruction

---

13. Stop Conditions

Agents MUST STOP if:

- A change alters calculation definitions
- PRD is unclear or conflicting
- Data assumptions are missing
- Behaviour would change unexpectedly

---

14. Future Scope (DO NOT IMPLEMENT)

The following are explicitly out of scope:

- Machine learning models
- Gradient boosting
- Automated hyperparameter tuning
- Reinforcement learning

---

15. Final Rule

If unsure:

«Do not guess. Follow the PRD or stop.»

---
