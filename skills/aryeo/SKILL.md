---
name: Aryeo Order Management
description: Capability to list and create orders in Aryeo using the aryeo_cli.py tool.
---

# Aryeo Order Management Skill

This skill allows you to interact with the Aryeo platform to manage real estate media orders.

## Tools

You should use the `aryeo_cli.py` script located in the root directory (`/home/ubuntu/.openclaw/workspace/aryeo_cli.py`) to perform actions.

### Usage

Run the script using `/home/ubuntu/.openclaw/workspace/venv/bin/python3 /home/ubuntu/.openclaw/workspace/aryeo_cli.py [command] [options]`.

### Commands

#### 1. List Orders
List the most recent orders.

```bash
python3 aryeo_cli.py orders list --limit 5
```

- `--limit`: (Optional) Number of orders to list (default: 5).

#### 2. Create Order
Create a new order. You need to provide a JSON string or file for the order data.

```bash
# Using a JSON string
python3 aryeo_cli.py orders create --data '{"fulfillment_status": "UNFULFILLED", "payment_status": "UNPAID", "customer_id": "UUID", "items": [{"id": "ITEM_UUID"}]}'
```

- `--data`: A JSON string containing the order details.

## Examples

**User Request:** "Show me the last 3 orders."
**Action:**
```bash
python3 aryeo_cli.py orders list --limit 3
```

**User Request:** "Create a new order for customer X."
**Action:**
1. First, you might need to find the customer ID (if not known). *Note: Customer search is not yet implemented in CLI, ask user for ID if unknown.*

#### 3. List Appointments
List the most recent appointments.

```bash
python3 aryeo_cli.py appointments list --limit 5
```

#### 4. Create Appointment
Schedule an appointment. Requires JSON data.

```bash
python3 aryeo_cli.py appointments create --data '{"start_at": "2026-02-10T10:00:00Z", "end_at": "2026-02-10T11:00:00Z", "order_id": "ORDER_UUID", "users": [{"id": "PHOTOGRAPHER_UUID"}]}'
```

- `--data`: JSON string with start/end times and order ID.

#### 5. Schedule Appointment (Browser Automation)
Use this command to schedule an appointment via browser automation (Deep Link). This is robust against API limitations.

**Note:** This script does NOT require sourcing any `.env` files. It runs standalone.

```bash
python3 scripts/schedule_aryeo_appt.py \
  --full-url "https://[DOMAIN].aryeo.com/admin/orders/[ORDER_UUID]" \
  --date "YYYY-MM-DD" \
  --time "HH:MM AM/PM" \
  --username "ARYEO_USERNAME" \
  --password "ARYEO_PASSWORD" \
  --package "Quick Click Package" 
```

- `--full-url`: The full URL to the Order page (e.g. `https://ctrealtymedia.aryeo.com/admin/orders/...`).
- `--package`: (Optional) Package to select (default: "Quick Click Package").
- `--headed`: (Optional) Run with visible browser for debugging.


