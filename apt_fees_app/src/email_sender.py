import base64

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Disposition, FileContent, FileName, FileType, Mail


def send_receipt_email(to_emails, subject, body, pdf_bytes, filename, sendgrid_key, from_email):
    if not sendgrid_key:
        return False, "Email not configured."
    if not to_emails:
        return False, "No recipient emails provided."

    message = Mail(
        from_email=from_email,
        to_emails=to_emails,
        subject=subject,
        plain_text_content=body,
    )

    if pdf_bytes:
        encoded = base64.b64encode(pdf_bytes).decode("utf-8")
        attachment = Attachment(
            FileContent(encoded),
            FileName(filename),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
        message.attachment = attachment

    try:
        client = SendGridAPIClient(sendgrid_key)
        client.send(message)
        return True, "Email sent."
    except Exception as exc:
        return False, f"Email failed: {exc}"
