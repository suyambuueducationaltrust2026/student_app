from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


def generate_receipt_pdf(receipt, student, fees):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 50

    # HEADER
    p.setFont("Helvetica-Bold", 32)
    p.drawString(75,y,"Suyambuu Learning Centre")
    y-=40
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, y, "FEE RECEIPT")
    y -= 40

    # STUDENT INFO
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Name: {student['name']}")
    y -= 20
    p.drawString(50, y, f"Course: {student['course_name']}")
    y -= 20
    p.drawString(50, y, f"Year: {student['year']}")
    y -= 30

    # RECEIPT INFO
    p.drawString(50, y, f"Receipt No: {receipt['receipt_no']}")
    y -= 20
    p.drawString(50, y, f"Payment Date: {receipt['payment_date']}")
    y -= 20
    p.drawString(50, y, f"Mode: {receipt['payment_mode']}")
    y -= 30

    # TABLE HEADER
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Fee Type")
    p.drawString(400, y, "Amount")
    y -= 20

    p.setFont("Helvetica", 11)

    total = 0

    for f in fees:
        p.drawString(50, y, f["fee_type"])
        p.drawString(400, y, str(f["amount"]))
        total += f["amount"]
        y -= 18

        if y < 100:
            p.showPage()
            y = height - 50

    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, f"Total Paid: ₹ {receipt['total_amount']}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer