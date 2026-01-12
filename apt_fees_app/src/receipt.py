import io

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def generate_receipt_pdf(payment, unit):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    width, height = LETTER
    x_left = 0.75 * inch
    y = height - 1.0 * inch

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x_left, y, "Maintenance Fee Receipt")

    y -= 0.4 * inch
    c.setFont("Helvetica", 11)

    fields = [
        ("Receipt ID", payment.get("receipt_id")),
        ("Unit ID", payment.get("unit_id")),
        ("Apartment", unit.get("apt_number")),
        ("Month", payment.get("month")),
        ("Amount", payment.get("amount")),
        ("Paid At", payment.get("paid_datetime")),
        ("Method", payment.get("payment_method")),
        ("Collected By", payment.get("collected_by")),
        ("Notes", payment.get("notes")),
    ]

    for label, value in fields:
        c.drawString(x_left, y, f"{label}: {value or ''}")
        y -= 0.25 * inch

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()
