import datetime as dt

import pandas as pd
import streamlit as st

from src import config, email_sender, receipt, repo_payments, repo_units, sheets_client, utils


st.set_page_config(page_title="Receipts", layout="wide")
st.title("Receipts")

spreadsheet_id = config.get_spreadsheet_id()
if not spreadsheet_id:
    st.error("Missing SPREADSHEET_ID in Streamlit secrets.")
    st.stop()

try:
    settings = sheets_client.get_settings(spreadsheet_id)
except Exception as exc:
    st.error(f"Settings load failed: {exc}")
    settings = {}

try:
    units = repo_units.list_units()
    payments = repo_payments.list_payments()
except Exception as exc:
    st.error(f"Data load failed: {exc}")
    st.stop()

unit_labels = {"All units": None}
for unit in units:
    label = f"{unit.get('unit_id')} - Apt {unit.get('apt_number')} - {unit.get('owner_name')}"
    unit_labels[label] = unit

selected_unit_label = st.selectbox("Unit", list(unit_labels.keys()))
selected_unit = unit_labels[selected_unit_label]

month_date = st.date_input("Month", value=dt.date.today().replace(day=1))
month_key = utils.month_key_from_date(month_date)

filtered = []
for payment in payments:
    if selected_unit and str(payment.get("unit_id")).strip() != str(
        selected_unit.get("unit_id")
    ).strip():
        continue
    if month_key and str(payment.get("month")) != str(month_key):
        continue
    filtered.append(payment)

df = pd.DataFrame(filtered)
st.dataframe(df, use_container_width=True, hide_index=True)

payment_options = {p.get("payment_id"): p for p in filtered if p.get("payment_id")}

if not payment_options:
    st.info("No receipts found for the selected filters.")
    st.stop()

selected_payment_id = st.selectbox("Select payment", list(payment_options.keys()))
payment = payment_options[selected_payment_id]
unit = repo_units.get_unit_by_id(payment.get("unit_id")) or {}

context = {
    "receipt_id": payment.get("receipt_id"),
    "unit_id": payment.get("unit_id"),
    "apt_number": unit.get("apt_number"),
    "month": payment.get("month"),
    "amount": payment.get("amount"),
    "paid_datetime": payment.get("paid_datetime"),
    "payment_method": payment.get("payment_method"),
    "collected_by": payment.get("collected_by"),
    "notes": payment.get("notes"),
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

pdf_bytes = receipt.generate_receipt_pdf(payment, unit)
st.download_button(
    "Download receipt PDF",
    data=pdf_bytes,
    file_name=f"{payment.get('receipt_id')}.pdf",
    mime="application/pdf",
)

if st.button("Resend receipt"):
    recipients = utils.safe_emails(unit.get("owner_email"), unit.get("tenant_email"))
    sendgrid_key = config.get_sendgrid_key()
    from_email = config.get_email_from()
    if not sendgrid_key:
        st.warning("Email not configured.")
    else:
        ok, msg = email_sender.send_receipt_email(
            recipients,
            subject,
            body,
            pdf_bytes,
            f"{payment.get('receipt_id')}.pdf",
            sendgrid_key,
            from_email,
        )
        if ok:
            try:
                repo_payments.update_payment(
                    payment.get("payment_id"),
                    {
                        "receipt_sent_to": "; ".join(recipients),
                        "receipt_sent_at": utils.now_utc_iso(),
                    },
                )
            except Exception as exc:
                st.error(f"Update failed: {exc}")
        st.success(msg) if ok else st.warning(msg)
