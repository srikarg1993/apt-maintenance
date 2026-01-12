import json

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

from src import config


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource
def get_client(service_account_info):
    if not service_account_info:
        raise ValueError("Missing service account info in Streamlit secrets.")
    if isinstance(service_account_info, str):
        service_account_info = json.loads(service_account_info)
    credentials = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(credentials)


def open_spreadsheet(spreadsheet_id):
    if not spreadsheet_id:
        raise ValueError("Missing SPREADSHEET_ID in Streamlit secrets.")
    client = get_client(config.get_service_account_info())
    return client.open_by_key(spreadsheet_id)


def get_worksheet(spreadsheet_id, sheet_name, create_if_missing=False):
    spreadsheet = open_spreadsheet(spreadsheet_id)
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        if not create_if_missing:
            raise ValueError(f"Missing sheet tab: {sheet_name}")
        return spreadsheet.add_worksheet(title=sheet_name, rows=2000, cols=30)


def ensure_headers(worksheet, expected_headers):
    existing_headers = worksheet.row_values(1)
    if not existing_headers:
        worksheet.update("1:1", [expected_headers])
        return expected_headers
    missing = [h for h in expected_headers if h not in existing_headers]
    if missing:
        raise ValueError(
            f"Missing columns in {worksheet.title}: {', '.join(missing)}"
        )
    return existing_headers


def initialize_sheet_headers(spreadsheet_id):
    sheets = {
        config.UNITS_SHEET: config.UNITS_HEADERS,
        config.PAYMENTS_SHEET: config.PAYMENTS_HEADERS,
        config.SETTINGS_SHEET: config.SETTINGS_HEADERS,
    }
    for name, headers in sheets.items():
        ws = get_worksheet(spreadsheet_id, name, create_if_missing=True)
        ensure_headers(ws, headers)


def get_headers(spreadsheet_id, sheet_name, expected_headers):
    ws = get_worksheet(spreadsheet_id, sheet_name, create_if_missing=False)
    return ensure_headers(ws, expected_headers)


def get_records(spreadsheet_id, sheet_name, expected_headers):
    ws = get_worksheet(spreadsheet_id, sheet_name, create_if_missing=False)
    headers = ensure_headers(ws, expected_headers)
    records = ws.get_all_records(expected_headers=headers)
    return records, headers


def append_row(spreadsheet_id, sheet_name, expected_headers, row_values):
    ws = get_worksheet(spreadsheet_id, sheet_name, create_if_missing=False)
    ensure_headers(ws, expected_headers)
    ws.append_row(row_values, value_input_option="USER_ENTERED")


def find_row_index_by_column(spreadsheet_id, sheet_name, expected_headers, col_name, value):
    ws = get_worksheet(spreadsheet_id, sheet_name, create_if_missing=False)
    headers = ensure_headers(ws, expected_headers)
    if col_name not in headers:
        raise ValueError(f"Missing column {col_name} in {sheet_name}.")
    col_index = headers.index(col_name) + 1
    values = ws.col_values(col_index)
    for idx, cell_value in enumerate(values, start=1):
        if idx == 1:
            continue
        if str(cell_value).strip() == str(value).strip():
            return idx
    return None


def column_index_to_letter(index):
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def update_row(spreadsheet_id, sheet_name, expected_headers, row_index, updates):
    ws = get_worksheet(spreadsheet_id, sheet_name, create_if_missing=False)
    headers = ensure_headers(ws, expected_headers)
    header_map = {h: i for i, h in enumerate(headers)}
    row_values = ws.row_values(row_index)
    row_data = {}
    for i, header in enumerate(headers):
        row_data[header] = row_values[i] if i < len(row_values) else ""
    for key, value in updates.items():
        if key not in header_map:
            raise ValueError(f"Missing column {key} in {sheet_name}.")
        row_data[key] = value
    new_row = [row_data.get(h, "") for h in headers]
    end_col = column_index_to_letter(len(headers))
    ws.update(f"A{row_index}:{end_col}{row_index}", [new_row])


@st.cache_data(ttl=15)
def get_settings_cached(spreadsheet_id):
    ws = get_worksheet(spreadsheet_id, config.SETTINGS_SHEET, create_if_missing=False)
    headers = ensure_headers(ws, config.SETTINGS_HEADERS)
    rows = ws.get_all_records(expected_headers=headers)
    if not rows:
        return {}
    return rows[0]


def get_settings(spreadsheet_id):
    return get_settings_cached(spreadsheet_id)
