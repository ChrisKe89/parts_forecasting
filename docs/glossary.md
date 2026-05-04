# Glossary

- **Service level:** Share of demand events fully fulfilled. In replay terms: `count(events with fulfilled_qty >= usage_qty) / count(events)`.
- **Fill rate:** Volume-based fulfilment ratio. `total_fulfilled_qty / total_usage_qty`.
- **MOQ (Minimum Order Quantity):** Smallest supplier-accepted order quantity for a part.
- **Order multiple:** Required pack increment (e.g., order in multiples of 5).
- **Lead time demand:** Expected demand consumed during replenishment lead time.
- **Safety stock:** Buffer inventory to protect against uncertainty.
- **Reorder point (ROP):** Trigger threshold for new orders. `reorder_point = lead_time_demand + safety_stock`.
- **Stockout:** Demand that cannot be fulfilled immediately from available stock.
- **Backorder:** Unfulfilled demand carried into subsequent periods.
- **Partial receipt:** Supplier delivery where only part of ordered quantity is received.
- **Delayed receipt:** Receipt not arriving by expected date; quantity remains open/on-order.
- **Forecast bias:** Directional tendency of forecast error (systematic over- or under-forecast).
- **MAE:** Mean Absolute Error of forecast values versus actual demand.
- **RMSE:** Root Mean Squared Error of forecast values versus actual demand.
- **Effective stock:** `stock_on_hand - allocated_qty - backorder_qty`.
- **Pipeline supply:** Open purchase order quantities arriving before planning need date.
- **Demand source (usage_only):** Replay/live mode demand basis that uses `usage_qty` only in this proof implementation.
