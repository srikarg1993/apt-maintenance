import os

import streamlit as st


UNITS_SHEET = "Units"
PAYMENTS_SHEET = "Payments"
SETTINGS_SHEET = "Settings"

UNITS_HEADERS = [
    "unit_id",
    "apt_number",
    "owner_name",
    "owner_email",
    "tenant_name",
    "tenant_email",
    "monthly_fee_default",
    "status",
    "notes",
]

PAYMENTS_HEADERS = [
    "payment_id",
    "unit_id",
    "month",
    "amount",
    "paid_datetime",
    "payment_method",
    "collected_by",
    "notes",
    "receipt_id",
    "receipt_pdf_url",
    "receipt_sent_to",
    "receipt_sent_at",
    "status",
]

SETTINGS_HEADERS = [
    "default_fee",
    "receipt_subject_template",
    "receipt_body_template",
    "admin_password",
    "email_provider",
]

DEFAULT_RECEIPT_SUBJECT = "Maintenance Receipt {month} - Unit {apt_number}"
DEFAULT_RECEIPT_BODY = (
    "Hello {owner_name},\n\n"
    "This is a receipt for the maintenance fee payment.\n\n"
    "Receipt ID: {receipt_id}\n"
    "Unit: {apt_number}\n"
    "Month: {month}\n"
    "Amount: {amount}\n"
    "Paid At: {paid_datetime}\n"
    "Method: {payment_method}\n"
    "Collected By: {collected_by}\n"
    "Notes: {notes}\n\n"
    "Thank you."
)


def get_secret(key, default=None):
    if key in st.secrets:
        return st.secrets.get(key)
    return os.getenv(key, default)


def get_spreadsheet_id():
    return get_secret("SPREADSHEET_ID")


def get_service_account_info():
    info = st.secrets.get("gcp_service_account")
    if info:
        return info
    raw = get_secret("GCP_SERVICE_ACCOUNT_JSON")
    if raw:
        try:
            import json

            return json.loads(raw)
        except Exception:
            return None
    return None


def get_sendgrid_key():
    return get_secret("SENDGRID_API_KEY")


def get_email_from():
    return get_secret("EMAIL_FROM", "no-reply@example.com")


def get_admin_password(settings=None):
    settings_password = None
    if settings:
        settings_password = (settings.get("admin_password") or "").strip()
    return settings_password or get_secret("ADMIN_PASSWORD")


def get_default_fee(settings=None):
    if settings:
        value = (settings.get("default_fee") or "").strip()
        if value:
            return value
    return get_secret("DEFAULT_FEE")
