from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


def generate_receipt_pdf(receipt, student, fees):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 40

    # HEADER
    p.setFont("Helvetica-Bold", 22)
    p.drawString(120, y,"SUYAMBUU EDUCATIONAL TRUST")
    y-=20
    p.setFont("Helvetica", 9)
    p.drawString(160, y, "No:1/160, Vallalar Street, Thirumalai Nagar,Anandalai Village & Post,")
    y-=10
    p.drawString(210,y,"Walajapet-632513. Ranipet District, Tamil Nadu.")
    y-=10
    p.drawString(180,y,"Cell: 9944135587 / 8248612310, E-mail: ppk.sset@gmail.com")
    y-=20
    p.setFont("Helvetica-Bold", 16)
    p.drawString(250, y, "FEE RECEIPT")
    y -= 30

    # STUDENT INFO
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Student Name: {student['name']}")
    p.drawString(400, y, f"Receipt No: {receipt['receipt_no']}")
    
    y -= 15
    
    p.drawString(50, y, f"Registration Number: {student['registration_no']}")
    p.drawString(400, y, f"Mobile No: {student['mobile']}")
    y -= 15
    p.drawString(50, y, f"University Name: {student['university_name']}")
    p.drawString(400, y, f"Payment Date: {receipt['payment_date']}")
    y -= 15
    p.drawString(50, y, f"Course: {student['course_name']}")
    p.drawString(400, y, f"Pattern: {student['pattern']}")
    y -= 15
    p.drawString(50, y, f"Admission Year: {student['year']}")
    p.drawString(400, y, f"Mode of Payment: {receipt['payment_mode']}")
    y -= 15
    p.drawString(50, y, f"Admission Type: {student['admission_type']}")
    p.drawString(400, y, f"Year/Sem: {receipt['yearfees_master']['course_year']}")
    y -= 15
    p.drawString(50, y, f"Program Name: {student['program_name']}")
    p.drawString(400, y, f"Reference No: {receipt['reference_number']}")
    y -= 20
    # RECEIPT INFO
    
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
    y -= 30
    p.drawString(50, y, f"Remarks: {receipt['remarks']}")
    y-=40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(375, y,"For Suyambuu Learning Centre")
    y-=40
    p.drawString(400, y,"Authorized Signatory")
    y-=50
    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer