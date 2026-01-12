import streamlit as st

from src import config, sheets_client, utils


@st.cache_data(ttl=15)
def list_units_cached(spreadsheet_id):
    records, _ = sheets_client.get_records(
        spreadsheet_id, config.UNITS_SHEET, config.UNITS_HEADERS
    )
    return records


def list_units():
    spreadsheet_id = config.get_spreadsheet_id()
    return list_units_cached(spreadsheet_id)


def get_unit_by_id(unit_id):
    for unit in list_units():
        if str(unit.get("unit_id")).strip() == str(unit_id).strip():
            return unit
    return None


def update_unit(unit_id, updates):
    spreadsheet_id = config.get_spreadsheet_id()
    row_index = sheets_client.find_row_index_by_column(
        spreadsheet_id, config.UNITS_SHEET, config.UNITS_HEADERS, "unit_id", unit_id
    )
    if not row_index:
        raise ValueError(f"Unit not found: {unit_id}")
    sheets_client.update_row(
        spreadsheet_id, config.UNITS_SHEET, config.UNITS_HEADERS, row_index, updates
    )
    st.cache_data.clear()


def add_unit(unit_data):
    spreadsheet_id = config.get_spreadsheet_id()
    row = [unit_data.get(h, "") for h in config.UNITS_HEADERS]
    sheets_client.append_row(spreadsheet_id, config.UNITS_SHEET, config.UNITS_HEADERS, row)
    st.cache_data.clear()


def unit_amount_due(unit, default_fee):
    fee = unit.get("monthly_fee_default")
    if fee:
        return utils.to_float(fee, utils.to_float(default_fee, 0.0))
    return utils.to_float(default_fee, 0.0)
