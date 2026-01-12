import streamlit as st

from src import config, sheets_client


SUCCESS_PREFIX = "SUCCESS"


@st.cache_data(ttl=15)
def list_payments_cached(spreadsheet_id):
    records, _ = sheets_client.get_records(
        spreadsheet_id, config.PAYMENTS_SHEET, config.PAYMENTS_HEADERS
    )
    return records


def list_payments():
    spreadsheet_id = config.get_spreadsheet_id()
    return list_payments_cached(spreadsheet_id)


def list_payments_for_month(month_key):
    return [p for p in list_payments() if str(p.get("month")) == str(month_key)]


def is_success_status(status):
    return str(status).upper().startswith(SUCCESS_PREFIX)


def latest_success_payment(unit_id, month_key):
    matches = [
        p
        for p in list_payments_for_month(month_key)
        if str(p.get("unit_id")).strip() == str(unit_id).strip()
        and is_success_status(p.get("status"))
    ]
    if not matches:
        return None
    matches.sort(key=lambda p: str(p.get("paid_datetime", "")))
    return matches[-1]


def add_payment(payment_data):
    spreadsheet_id = config.get_spreadsheet_id()
    row = [payment_data.get(h, "") for h in config.PAYMENTS_HEADERS]
    sheets_client.append_row(
        spreadsheet_id, config.PAYMENTS_SHEET, config.PAYMENTS_HEADERS, row
    )
    st.cache_data.clear()


def update_payment(payment_id, updates):
    spreadsheet_id = config.get_spreadsheet_id()
    row_index = sheets_client.find_row_index_by_column(
        spreadsheet_id,
        config.PAYMENTS_SHEET,
        config.PAYMENTS_HEADERS,
        "payment_id",
        payment_id,
    )
    if not row_index:
        raise ValueError(f"Payment not found: {payment_id}")
    sheets_client.update_row(
        spreadsheet_id,
        config.PAYMENTS_SHEET,
        config.PAYMENTS_HEADERS,
        row_index,
        updates,
    )
    st.cache_data.clear()
