import streamlit as st
import pandas as pd

from src import config, repo_units, sheets_client, utils


st.set_page_config(page_title="Admin", layout="wide")
st.title("Admin")

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
if not utils.require_password("admin", admin_password):
    st.stop()

col1, col2 = st.columns(2)
with col1:
    if st.button("Initialize sheet headers"):
        try:
            sheets_client.initialize_sheet_headers(spreadsheet_id)
            st.success("Headers initialized.")
        except Exception as exc:
            st.error(f"Init failed: {exc}")
with col2:
    if st.button("Refresh data"):
        st.cache_data.clear()

try:
    units = repo_units.list_units()
except Exception as exc:
    st.error(f"Units load failed: {exc}")
    st.stop()

st.subheader("Units")
st.dataframe(pd.DataFrame(units), use_container_width=True, hide_index=True)

unit_map = {
    f"{u.get('unit_id')} - Apt {u.get('apt_number')} - {u.get('owner_name')}": u
    for u in units
}

if not unit_map:
    st.info("No units available.")
    st.stop()

selected_label = st.selectbox("Edit unit", list(unit_map.keys()))
unit = unit_map[selected_label]

with st.form("edit_unit_form"):
    tenant_name = st.text_input("Tenant name", value=unit.get("tenant_name", ""))
    tenant_email = st.text_input("Tenant email", value=unit.get("tenant_email", ""))
    monthly_fee_default = st.text_input(
        "Monthly fee", value=str(unit.get("monthly_fee_default", ""))
    )
    status = st.text_input("Status", value=unit.get("status", "ACTIVE"))
    notes = st.text_area("Notes", value=unit.get("notes", ""))
    submitted = st.form_submit_button("Save changes")

if submitted:
    try:
        repo_units.update_unit(
            unit.get("unit_id"),
            {
                "tenant_name": tenant_name,
                "tenant_email": tenant_email,
                "monthly_fee_default": monthly_fee_default,
                "status": status,
                "notes": notes,
            },
        )
        st.success("Unit updated.")
    except Exception as exc:
        st.error(f"Update failed: {exc}")

st.subheader("Add unit")
with st.form("add_unit_form"):
    new_unit_id = st.text_input("Unit ID", value="")
    new_apt_number = st.text_input("Apartment number", value="")
    new_owner_name = st.text_input("Owner name", value="")
    new_owner_email = st.text_input("Owner email", value="")
    new_tenant_name = st.text_input("Tenant name (optional)", value="")
    new_tenant_email = st.text_input("Tenant email (optional)", value="")
    new_monthly_fee = st.text_input("Monthly fee", value="")
    new_status = st.text_input("Status", value="ACTIVE")
    new_notes = st.text_area("Notes", value="")
    add_submitted = st.form_submit_button("Add unit")

if add_submitted:
    if not new_unit_id or not new_owner_name:
        st.error("Unit ID and owner name are required.")
    else:
        try:
            repo_units.add_unit(
                {
                    "unit_id": new_unit_id,
                    "apt_number": new_apt_number,
                    "owner_name": new_owner_name,
                    "owner_email": new_owner_email,
                    "tenant_name": new_tenant_name,
                    "tenant_email": new_tenant_email,
                    "monthly_fee_default": new_monthly_fee,
                    "status": new_status,
                    "notes": new_notes,
                }
            )
            st.success("Unit added.")
        except Exception as exc:
            st.error(f"Add failed: {exc}")
