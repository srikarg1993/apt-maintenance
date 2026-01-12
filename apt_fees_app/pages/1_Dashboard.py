import datetime as dt

import pandas as pd
import streamlit as st

from src import config, repo_payments, repo_units, sheets_client, utils


st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Dashboard")

spreadsheet_id = config.get_spreadsheet_id()
if not spreadsheet_id:
    st.error("Missing SPREADSHEET_ID in Streamlit secrets.")
    st.stop()

default_date = dt.date.today().replace(day=1)
month_date = st.date_input("Month", value=default_date)
month_key = utils.month_key_from_date(month_date)

if st.button("Refresh"):
    st.cache_data.clear()

try:
    settings = sheets_client.get_settings(spreadsheet_id)
except Exception as exc:
    st.error(f"Settings load failed: {exc}")
    settings = {}

default_fee = utils.to_float(config.get_default_fee(settings), 0.0)

try:
    units = repo_units.list_units()
    payments = repo_payments.list_payments_for_month(month_key)
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

paid_map = {}
for payment in payments:
    if not repo_payments.is_success_status(payment.get("status")):
        continue
    unit_id = str(payment.get("unit_id", "")).strip()
    if not unit_id:
        continue
    current = paid_map.get(unit_id)
    if not current or str(payment.get("paid_datetime", "")) > str(
        current.get("paid_datetime", "")
    ):
        paid_map[unit_id] = payment

total_units = len(units)
paid_count = len(paid_map)
unpaid_count = max(total_units - paid_count, 0)

total_collected = sum(utils.to_float(p.get("amount"), 0.0) for p in paid_map.values())
outstanding_amount = 0.0

rows = []
for unit in units:
    unit_id = unit.get("unit_id")
    amount_due = repo_units.unit_amount_due(unit, default_fee)
    payment = paid_map.get(str(unit_id).strip())
    if not payment:
        outstanding_amount += amount_due
    rows.append(
        {
            "unit_id": unit_id,
            "apt_number": unit.get("apt_number"),
            "owner_name": unit.get("owner_name"),
            "tenant_name": unit.get("tenant_name"),
            "status": "PAID" if payment else "UNPAID",
            "amount_due": amount_due,
            "amount_paid": payment.get("amount") if payment else "",
            "paid_datetime": payment.get("paid_datetime") if payment else "",
            "payment_method": payment.get("payment_method") if payment else "",
            "receipt_id": payment.get("receipt_id") if payment else "",
        }
    )

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Units", total_units)
col2.metric("Paid", paid_count)
col3.metric("Unpaid", unpaid_count)
col4.metric("Collected", utils.format_currency(total_collected))
col5.metric("Outstanding", utils.format_currency(outstanding_amount))

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)
