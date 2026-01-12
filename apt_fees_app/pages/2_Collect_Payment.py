import datetime as dt

import streamlit as st

from src import config, email_sender, receipt, repo_payments, repo_units, sheets_client, utils


st.set_page_config(page_title="Collect Payment", layout="wide")
st.title("Collect Payment")

spreadsheet_id = config.get_spreadsheet_id()
if not spreadsheet_id:
    st.error("Missing SPREADSHEET_ID in Streamlit secrets.")
    st.stop()

try:
    settings = sheets_client.get_settings(spreadsheet_id)
except Exception as exc:
    st.error(f"Settings load failed: {exc}")
    settings = {}

admin_password = config.get_admin_password(settings)
if not utils.require_password("collect_payment", admin_password):
    st.stop()

default_fee = utils.to_float(config.get_default_fee(settings), 0.0)

try:
    units = repo_units.list_units()
except Exception as exc:
    st.error(f"Units load failed: {exc}")
    st.stop()

if not units:
    st.warning("No units found in the Units sheet.")
    st.stop()

unit_options = {
    f"{u.get('unit_id')} - Apt {u.get('apt_number')} - {u.get('owner_name')}": u
    for u in units
}

month_date = st.date_input("Month", value=dt.date.today().replace(day=1))
month_key = utils.month_key_from_date(month_date)

selected_label = st.selectbox("Select unit", list(unit_options.keys()))
unit = unit_options[selected_label]

default_amount = repo_units.unit_amount_due(unit, default_fee)

amount = st.number_input("Amount", min_value=0.0, value=float(default_amount), step=1.0)
payment_method = st.selectbox("Payment method", ["Cash", "UPI", "Bank Transfer", "Cheque", "Other"])
collected_by = st.text_input("Collected by", value="Admin")
notes = st.text_area("Notes", value="")
payer = st.text_input("Payer (optional)", value="")

duplicate = repo_payments.latest_success_payment(unit.get("unit_id"), month_key)
allow_override = False
if duplicate:
    st.warning(
        f"Payment already exists for {unit.get('unit_id')} in {month_key}. "
        "Enable override to record another payment."
    )
    allow_override = st.checkbox("Override duplicate and record payment", value=False)

if st.button("Submit payment"):
    if duplicate and not allow_override:
        st.error("Duplicate payment not allowed without override.")
        st.stop()

    receipt_id = f"APT-{month_key}-{unit.get('unit_id')}-{utils.short_id()}"
    payment_id = f"PAY-{month_key}-{unit.get('unit_id')}-{utils.short_id()}"
    paid_datetime = utils.now_utc_iso()

    note_text = notes or ""
    if payer:
        note_text = f"Payer: {payer}. {note_text}".strip()

    payment_data = {
        "payment_id": payment_id,
        "unit_id": unit.get("unit_id"),
        "month": month_key,
        "amount": f"{amount:.2f}",
        "paid_datetime": paid_datetime,
        "payment_method": payment_method,
        "collected_by": collected_by,
        "notes": note_text,
        "receipt_id": receipt_id,
        "receipt_pdf_url": "",
        "receipt_sent_to": "",
        "receipt_sent_at": "",
        "status": "PENDING",
    }

    try:
        repo_payments.add_payment(payment_data)
    except Exception as exc:
        st.error(f"Payment save failed: {exc}")
        st.stop()

    pdf_bytes = receipt.generate_receipt_pdf(payment_data, unit)

    context = {
        "receipt_id": receipt_id,
        "unit_id": unit.get("unit_id"),
        "apt_number": unit.get("apt_number"),
        "month": month_key,
        "amount": f"{amount:.2f}",
        "paid_datetime": paid_datetime,
        "payment_method": payment_method,
        "collected_by": collected_by,
        "notes": note_text,
        "owner_name": unit.get("owner_name"),
    }

    subject = utils.build_receipt_subject(
        settings.get("receipt_subject_template"),
        context,
        config.DEFAULT_RECEIPT_SUBJECT,
    )
    body = utils.build_receipt_body(
        settings.get("receipt_body_template"),
        context,
        config.DEFAULT_RECEIPT_BODY,
    )

    recipients = utils.safe_emails(unit.get("owner_email"), unit.get("tenant_email"))
    sendgrid_key = config.get_sendgrid_key()
    from_email = config.get_email_from()

    email_ok = False
    email_msg = ""
    if sendgrid_key:
        email_ok, email_msg = email_sender.send_receipt_email(
            recipients,
            subject,
            body,
            pdf_bytes,
            f"{receipt_id}.pdf",
            sendgrid_key,
            from_email,
        )
    else:
        email_msg = "Email not configured."

    status_base = "SUCCESS_OVERRIDE" if allow_override else "SUCCESS"
    if not sendgrid_key:
        status = f"{status_base}_EMAIL_NOT_CONFIGURED"
    elif email_ok:
        status = status_base
    else:
        status = f"{status_base}_EMAIL_FAILED"

    updates = {
        "receipt_sent_to": "; ".join(recipients),
        "receipt_sent_at": utils.now_utc_iso() if email_ok else "",
        "status": status,
    }

    try:
        repo_payments.update_payment(payment_id, updates)
    except Exception as exc:
        st.error(f"Payment update failed: {exc}")

    st.success("Payment recorded.")
    if email_ok:
        st.success(email_msg)
    else:
        st.warning(email_msg)

    st.download_button(
        "Download receipt PDF",
        data=pdf_bytes,
        file_name=f"{receipt_id}.pdf",
        mime="application/pdf",
    )
