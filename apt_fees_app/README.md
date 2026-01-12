# Apartment Maintenance Fee Tracker (Streamlit MVP)

This is an MVP Streamlit app that tracks monthly maintenance fee payments for an apartment complex using Google Sheets as the backend.

Assumptions for this MVP:
- The spreadsheet has three tabs named exactly: `Units`, `Payments`, `Settings`.
- Each tab uses a single header row (row 1). Settings are stored in row 2 (one row of values).
- Unit IDs are unique and stable (for example, `U01`, `U02`, ...).
- Payments are append-only; edits happen by updating the same row by `payment_id`.

## Project structure

```
apt_fees_app/
  app.py
  pages/
    1_Dashboard.py
    2_Collect_Payment.py
    3_Receipts.py
    4_Admin.py
  src/
    config.py
    sheets_client.py
    repo_units.py
    repo_payments.py
    receipt.py
    email_sender.py
    utils.py
  requirements.txt
  README.md
```

## Google Sheets setup

1) Create a Google Cloud Project.
2) Enable Google Sheets API and Google Drive API.
3) Create a Service Account and download its JSON key.
4) Create a Google Sheet and add three tabs: `Units`, `Payments`, `Settings`.
5) Share the sheet with the service account email (Editor access).

### Required headers

Units tab columns:
```
unit_id, apt_number, owner_name, owner_email, tenant_name, tenant_email, monthly_fee_default, status, notes
```

Payments tab columns:
```
payment_id, unit_id, month, amount, paid_datetime, payment_method, collected_by, notes,
receipt_id, receipt_pdf_url, receipt_sent_to, receipt_sent_at, status
```

Settings tab columns (single row of values):
```
default_fee, receipt_subject_template, receipt_body_template, admin_password, email_provider
```

The app includes a helper button to initialize headers if a tab is empty.

## Streamlit secrets

Create `.streamlit/secrets.toml` locally (do not commit). Example:

```toml
SPREADSHEET_ID = "your_spreadsheet_id"
ADMIN_PASSWORD = "replace_me"
EMAIL_FROM = "no-reply@yourdomain.com"
SENDGRID_API_KEY = "SG.xxxxx"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "xxxxx"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "service-account@your-project.iam.gserviceaccount.com"
client_id = "1234567890"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

Notes:
- `ADMIN_PASSWORD` can also be provided in the Settings tab if you do not want to store it in secrets.
- If `SENDGRID_API_KEY` is missing, the app still works and shows "Email not configured"; receipts remain downloadable.
- Receipt templates use Python `str.format` with keys like `{receipt_id}`, `{apt_number}`, `{month}`, `{amount}`.
- The optional payer field is appended into the payment `notes` column.

## Running locally

```bash
cd apt_fees_app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

1) Push this repo to GitHub.
2) Create a Streamlit Cloud app pointed at `apt_fees_app/app.py`.
3) Add the contents of `secrets.toml` in Streamlit Cloud settings.

## Usage tips

- Use the Dashboard to monitor paid vs unpaid units for a selected month.
- Use Collect Payment to log a payment, generate a receipt, and email it.
- Receipts page allows search and resend.
- Admin page lets you edit tenant info, fees, and status.
