import streamlit as st

from src import config, sheets_client


st.set_page_config(
    page_title="Apartment Maintenance Tracker",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Apartment Maintenance Fee Tracker")
st.write(
    "Use the pages in the left sidebar to manage payments, receipts, and unit data."
)

spreadsheet_id = config.get_spreadsheet_id()
if not spreadsheet_id:
    st.error("Missing SPREADSHEET_ID in Streamlit secrets.")

with st.sidebar:
    st.header("Setup")
    if st.button("Initialize sheet headers"):
        try:
            sheets_client.initialize_sheet_headers(spreadsheet_id)
            st.success("Headers initialized.")
        except Exception as exc:
            st.error(f"Init failed: {exc}")

st.subheader("Quick checks")
col1, col2 = st.columns(2)
with col1:
    st.write("Spreadsheet ID")
    st.code(spreadsheet_id or "Not configured")
with col2:
    st.write("Service account")
    service_info = config.get_service_account_info()
    st.code(service_info.get("client_email") if service_info else "Not configured")

st.info(
    "Tip: If tabs are empty, use 'Initialize sheet headers' to set up required columns."
)
