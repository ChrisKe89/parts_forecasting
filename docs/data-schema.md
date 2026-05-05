# Data Schema Contract

## Global Rules

- Inputs are CSV files with headers exactly matching the documented column names.
- Required files must exist and include all required columns.
- Optional files may be absent; if present, they must match schema.
- No generic column names such as `date` or `qty`.

## Required Files

- `parts_master.csv`
- `part_model_mapping.csv`
- `internal_parts_usage.csv`
- `orders.csv`
- `stock_snapshot.csv`
- `open_purchase_orders.csv`
- `active_machine_population.csv`

## Optional File

- `install_forecast.csv`

## 1) parts_master.csv

**Purpose:** Part attributes and planning defaults.

**Required columns:**
`part_number,part_description,smoothing_group,minimum_order_qty,default_lead_time_days,is_active`

**Allowed values / rules:**

- `minimum_order_qty >= 0`
- `default_lead_time_days > 0`
- `is_active` boolean-like (`true/false`, `1/0`, or canonical boolean)

**Example row:**
`P-1001,Hydraulic Seal,A,10,45,true`

**Validation:** Unique `part_number`; no null required fields.

## 2) part_model_mapping.csv

**Purpose:** Defines compatible model relationships per part.

**Required columns:**
`part_number,model`

**Example row:**
`P-1001,EX200`

**Validation:** `(part_number, model)` pair unique; `part_number` must exist in `parts_master.csv`.

## 3) internal_parts_usage.csv

**Purpose:** Internal service usage demand history.

**Required columns:**
`part_number,model,usage_date,usage_qty`

**Optional columns:**
`machine_serial,service_order_no,technician_id`

**Allowed values / rules:**

- `usage_qty >= 0`
- `usage_date` valid date

**Example row:**
`P-1001,EX200,2026-01-15,3,SN-77881,SO-5123,T-91`

**Validation:** `part_number`/`model` should match `part_model_mapping.csv`; unknown mappings generate warnings.

## 4) orders.csv

**Purpose:** Sales/service order activity and fulfilment.

**Required columns:**
`order_no,part_number,order_qty,fulfilled_qty,order_date,order_source,order_status,order_fulfilment_date`

**Allowed `order_source`:**
`dealer,direct,internal,other`

**Allowed `order_status`:**
`fulfilled,partially_fulfilled,backorder,cancelled`

**Derived fields:**

- `unfulfilled_qty = order_qty - fulfilled_qty`
- `backorder_qty = sum(unfulfilled_qty where order_status in partially_fulfilled/backorder)`

**Demand rule:**
Dealer orders are part-level demand. Direct/internal orders are not counted as forecast demand if usage is already represented in `internal_parts_usage.csv`.

**Example row:**
`O-9001,P-1001,12,7,2026-02-01,dealer,partially_fulfilled,2026-02-10`

**Validation:** quantities non-negative; `fulfilled_qty <= order_qty`.

## 5) stock_snapshot.csv

**Purpose:** Current inventory position and committed allocation.

**Required columns:**
`part_number,stock_snapshot_date,stock_on_hand_qty,allocated_qty`

**Derived fields:**

- `available_stock_qty = stock_on_hand_qty - allocated_qty`
- `effective_stock_qty = stock_on_hand_qty - allocated_qty - backorder_qty`

**Example row:**
`P-1001,2026-03-01,150,40`

**Validation:** quantities non-negative.

## 6) open_purchase_orders.csv

**Purpose:** Inbound purchase pipeline.

**Required columns:**
`purchase_order_no,part_number,purchase_order_qty,received_qty,open_purchase_order_qty,purchase_order_date,purchase_order_status,expected_arrival_date`

**Allowed `purchase_order_status`:**
`open,partially_received,received,cancelled`

**Validation:**

- `open_purchase_order_qty = purchase_order_qty - received_qty`
- Quantities non-negative

**Example row:**
`PO-221,P-1001,300,120,180,2026-02-20,partially_received,2026-04-15`

## 7) active_machine_population.csv

**Purpose:** Active installed base by model.

**Required columns:**
`model,population_snapshot_date,active_machine_qty,owner_group,service_group`

**Allowed `owner_group`:**
`direct,customer,dealer`

**Allowed `service_group`:**
`direct,dealer`

**Example row:**
`EX200,2026-03-01,480,customer,dealer`

**Validation:** `active_machine_qty >= 0`; valid date.

## 8) install_forecast.csv (Optional)

**Purpose:** Future install activity for demand adjustment.

**Required columns (if provided):**
`model,install_date,install_qty,install_status,projected_install_confidence`

**Allowed `install_status`:**
`scheduled,projected,cancelled`

**Rules:**

- scheduled installs count at 100%
- projected installs weighted by `projected_install_confidence`
- cancelled installs ignored

**Example row:**
`EX200,2026-05-10,25,projected,0.65`

**Validation:** `install_qty >= 0`; confidence in `[0,1]` for projected rows.

## Column Input Domain Summary

The following constrained columns enforce finite input domains:

- `orders.csv.order_source`: `dealer`, `direct`, `internal`, `other`
- `orders.csv.order_status`: `fulfilled`, `partially_fulfilled`, `backorder`, `cancelled`
- `open_purchase_orders.csv.purchase_order_status`: `open`, `partially_received`, `received`, `cancelled`
- `active_machine_population.csv.owner_group`: `direct`, `customer`, `dealer`
- `active_machine_population.csv.service_group`: `direct`, `dealer`
- `install_forecast.csv.install_status`: `scheduled`, `projected`, `cancelled`
- `install_forecast.csv.projected_install_confidence`: numeric in `[0,1]`

Arithmetic constraints:

- `orders.csv.fulfilled_qty <= orders.csv.order_qty`
- `open_purchase_orders.csv.open_purchase_order_qty = purchase_order_qty - received_qty`
