import datetime as dt
import random
import string

import streamlit as st


def now_utc_iso():
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def month_key_from_date(value):
    if isinstance(value, dt.date):
        return value.strftime("%Y-%m")
    return dt.datetime.utcnow().strftime("%Y-%m")


def short_id(length=6):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def format_currency(value):
    return f"{value:,.2f}"


def require_password(page_key, admin_password):
    if not admin_password:
        st.warning("Admin password is not configured.")
        return False
    state_key = f"auth_{page_key}"
    if st.session_state.get(state_key):
        return True
    with st.form(f"auth_form_{page_key}"):
        pwd = st.text_input("Admin password", type="password")
        submitted = st.form_submit_button("Unlock")
    if submitted:
        if pwd == admin_password:
            st.session_state[state_key] = True
            st.success("Unlocked.")
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


def safe_emails(*values):
    emails = []
    for value in values:
        if not value:
            continue
        item = value.strip()
        if item:
            emails.append(item)
    return list(dict.fromkeys(emails))


def build_receipt_subject(template, context, default_template):
    try:
        return template.format(**context) if template else default_template.format(**context)
    except Exception:
        return default_template.format(**context)


def build_receipt_body(template, context, default_template):
    try:
        return template.format(**context) if template else default_template.format(**context)
    except Exception:
        return default_template.format(**context)
