"""
Fee receipt PDF (A4) - SUYAMBUU LEARNING CENTRE.
Design from receipt_generator.py (Indigo & Amber theme).
Assets (optional): assets/logo.jpg and assets/signature.png
(signature.png should have a transparent background).
"""
import os
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

BASE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(BASE, "assets", "logo.jpg")
SIGNATURE = os.path.join(BASE, "assets", "signature.png")

# ------------------------------------------------------------------ CONFIG
CENTRE = {
    "name": "SUYAMBUU LEARNING CENTRE",
    "address1": "NO. 46 & 47, KONERI CHETTY STREET, ANAICUT ROAD,",
    "address2": "WALAJAPET, RANIPET DISTRICT - 632513, TAMILNADU",
    "contact": "CELL: +919944135587 / +918248612310",
    "email": "suyambuulearningcentre@gmail.com",
}

# Indigo & Amber theme
PRIMARY = colors.HexColor("#3730A3")
ACCENT = colors.HexColor("#F59E0B")
LIGHT = colors.HexColor("#EEF2FF")
GREY = colors.HexColor("#6B7280")
LINE = colors.HexColor("#C7D2FE")


# ------------------------------------------------------------- HELPERS
def amount_in_words(n: int) -> str:
    """Indian numbering system, e.g. 100 -> One Hundred Rupees Only."""
    ones = ("Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
            "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen").split()
    tens = "_ _ Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split()

    def below100(x):
        return ones[x] if x < 20 else tens[x // 10] + (" " + ones[x % 10] if x % 10 else "")

    def below1000(x):
        s = ""
        if x >= 100:
            s = ones[x // 100] + " Hundred"
            x %= 100
            if x:
                s += " "
        return s + (below100(x) if x else "")

    if n == 0:
        return "Zero Rupees Only"
    parts = []
    for div, label in ((10000000, "Crore"), (100000, "Lakh"), (1000, "Thousand")):
        if n >= div:
            parts.append(below1000(n // div) + " " + label)
            n %= div
    if n:
        parts.append(below1000(n))
    return " ".join(parts) + " Rupees Only"


def fmt_date(s) -> str:
    """Show dates as dd/mm/yyyy."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(s)[:19], fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return str(s)


def draw_image_if_exists(c, path, x, y, w, h):
    if os.path.exists(path):
        c.drawImage(ImageReader(path), x, y, w, h, preserveAspectRatio=True, mask="auto")


def field(c, x, y, w, label, value):
    """Small grey label above a bold value with a thin underline."""
    c.setFillColor(GREY)
    c.setFont("Helvetica", 7.5)
    c.drawString(x, y, label.upper())
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(x, y - 5.5 * mm, str(value) if value not in (None, "") else "-")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(x, y - 7.5 * mm, x + w, y - 7.5 * mm)


# -------------------------------------------------------------- RECEIPT
def draw_receipt(c, d, top):
    """Draws one receipt. The border is sized to the content (fee rows vary)."""
    W, _ = A4
    L = 15 * mm
    R = W - 15 * mm
    CW = R - L
    PAD = 8 * mm
    mid = (L + R) / 2
    y = top

    # ---- Header: logo left, centre details centred on the remaining width
    hh = 38 * mm
    logo = 31 * mm
    draw_image_if_exists(c, LOGO, L + 6 * mm, y - 4 * mm - logo, logo, logo)
    tcx = (L + 6 * mm + logo + R - 6 * mm) / 2
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 19)
    c.drawCentredString(tcx, y - 13 * mm, CENTRE["name"])
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.2)
    c.line(tcx - 32 * mm, y - 16 * mm, tcx + 32 * mm, y - 16 * mm)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(tcx, y - 21 * mm, CENTRE["address1"])
    c.drawCentredString(tcx, y - 25.5 * mm, CENTRE["address2"])
    c.drawCentredString(tcx, y - 30 * mm, CENTRE["contact"])
    c.drawCentredString(tcx, y - 34.5 * mm, CENTRE["email"])
    y -= hh
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.5)
    c.line(L + 1.5 * mm, y, R - 1.5 * mm, y)

    # ---- Centred title with letter spacing
    y -= 10 * mm
    title = "FEE RECEIPT"
    c.setFont("Helvetica-Bold", 16)
    tw_ = c.stringWidth(title, "Helvetica-Bold", 16) + len(title) * 2
    c.saveState()
    t = c.beginText(mid - tw_ / 2, y)
    t.setFont("Helvetica-Bold", 16)
    t.setCharSpace(2)
    t.setFillColor(PRIMARY)
    t.textLine(title)
    c.drawText(t)
    c.restoreState()    # drops the letter-spacing so later text is normal
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.8)
    c.line(L + PAD, y + 2 * mm, mid - tw_ / 2 - 5 * mm, y + 2 * mm)
    c.line(mid + tw_ / 2 + 5 * mm, y + 2 * mm, R - PAD, y + 2 * mm)

    # ---- Receipt no / date / mode (three equal boxes, full width)
    y -= 8 * mm
    gap = 3 * mm
    bw = (CW - 2 * PAD - 2 * gap) / 3
    bh = 12 * mm
    items = [("Receipt No", d["receipt_no"]),
             ("Payment Date", fmt_date(d["payment_date"])),
             ("Mode of Payment", d["mode"])]
    for i, (lab, val) in enumerate(items):
        x0 = L + PAD + i * (bw + gap)
        c.setFillColor(LIGHT)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.roundRect(x0, y - bh, bw, bh, 1.5 * mm, stroke=1, fill=1)
        c.setFillColor(GREY)
        c.setFont("Helvetica", 7)
        c.drawString(x0 + 3 * mm, y - 4 * mm, lab.upper())
        c.setFillColor(PRIMARY)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x0 + 3 * mm, y - 9.5 * mm, str(val))
    y -= bh + 8 * mm

    # ---- Student details
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(L + PAD, y, "STUDENT DETAILS")
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1)
    c.line(L + PAD, y - 1.5 * mm, L + PAD + 32 * mm, y - 1.5 * mm)

    rows = [
        (("Student Name", d["student_name"]), ("Application Number", d["application_no"])),
        (("Registration Number", d["registration_no"]), ("Mobile No", d["mobile"])),
        (("University Name", d["university"]), ("Course", d["course"])),
        (("Program Name", d["program"]), ("Pattern", d["pattern"])),
        (("Admission Year", d["admission_year"]), ("Admission Type", d["admission_type"])),
        (("Year / Sem", d["year_sem"]), ("Reference No", d["reference_no"])),
    ]
    col_w = (CW - 2 * PAD - 10 * mm) / 2
    x1 = L + PAD
    x2 = x1 + col_w + 10 * mm
    y -= 9 * mm
    for left, right in rows:
        field(c, x1, y, col_w, *left)
        field(c, x2, y, col_w, *right)
        y -= 11.5 * mm

    # ---- Fee table (any number of rows)
    y -= 1 * mm
    tx, tw = L + PAD, CW - 2 * PAD
    c.setFillColor(PRIMARY)
    c.rect(tx, y - 6.5 * mm, tw, 7 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(tx + 3 * mm, y - 4.5 * mm, "S.NO")
    c.drawString(tx + 18 * mm, y - 4.5 * mm, "FEE TYPE")
    c.drawRightString(tx + tw - 3 * mm, y - 4.5 * mm, "AMOUNT (Rs.)")
    y -= 6.5 * mm
    for i, (name, amt) in enumerate(d["fees"], 1):
        y -= 7 * mm
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(tx + 3 * mm, y + 2 * mm, str(i))
        c.drawString(tx + 18 * mm, y + 2 * mm, name)
        c.drawRightString(tx + tw - 3 * mm, y + 2 * mm, f"{amt:,.2f}")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(tx, y, tx + tw, y)
    y -= 8 * mm
    c.setFillColor(LIGHT)
    c.rect(tx, y, tw, 8 * mm, stroke=0, fill=1)
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(tx + 18 * mm, y + 2.5 * mm, "TOTAL PAID")
    c.drawRightString(tx + tw - 3 * mm, y + 2.5 * mm, f"Rs. {d['total']:,.2f}")
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1)
    c.line(tx, y, tx + tw, y)

    # ---- Amount in words + remarks
    y -= 7 * mm
    c.setFillColor(GREY)
    c.setFont("Helvetica", 8)
    c.drawString(tx, y, "AMOUNT IN WORDS:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-BoldOblique", 10)
    c.drawString(tx + 30 * mm, y, amount_in_words(int(d["total"])))
    y -= 6 * mm
    c.setFillColor(GREY)
    c.setFont("Helvetica", 8)
    c.drawString(tx, y, "REMARKS:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(tx + 30 * mm, y, d["remarks"])

    # ---- Signature (image sits on the line)
    sy = y - 28 * mm
    sw = 40 * mm
    sig_x = R - PAD - 27 * mm
    if os.path.exists(SIGNATURE):
        sig = ImageReader(SIGNATURE)
        iw, ih = sig.getSize()
        sh = sw * ih / iw
        c.drawImage(sig, sig_x - sw / 2, sy + 1 * mm, sw, sh, mask="auto")
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    c.line(R - PAD - 54 * mm, sy, R - PAD, sy)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(sig_x, sy - 4.5 * mm, "Authorized Signatory")
    c.setFont("Helvetica", 8)
    c.setFillColor(GREY)
    c.drawCentredString(sig_x, sy - 8.5 * mm, "For " + CENTRE["name"].title())

    # ---- Rounded border drawn last so it fits the content height
    bottom = sy - 14 * mm
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1.4)
    c.roundRect(L, bottom, CW, top - bottom, 4 * mm)


# ------------------------------------------------------------ PUBLIC API
def build_receipt_data(receipt, student, fees):
    """Map the app's receipt / student / fee rows to the layout fields."""
    fee_rows = [(f["fee_type"], float(f["amount"] or 0)) for f in fees]
    total = float(receipt.get("total_amount") or 0)

    # Late-payment fine is stored in the total but not in the fee rows
    fine = round(total - sum(a for _, a in fee_rows), 2)
    if fine > 0:
        fee_rows.append(("LATE PAYMENT FINE", fine))

    course_year = (receipt.get("yearfees_master") or {}).get("course_year")

    return {
        "receipt_no": receipt.get("receipt_no") or "",
        "payment_date": receipt.get("payment_date") or "",
        "mode": receipt.get("payment_mode") or "-",
        "student_name": student.get("name") or "-",
        "application_no": student.get("application_no") or "-",
        "registration_no": student.get("registration_no") or "-",
        "mobile": student.get("mobile") or "-",
        "university": student.get("university_name") or "-",
        "course": student.get("course_name") or "-",
        "program": student.get("program_name") or "-",
        "pattern": student.get("pattern") or "-",
        "admission_year": student.get("year") or "-",
        "admission_type": student.get("admission_type") or "-",
        "year_sem": course_year or "-",
        "reference_no": receipt.get("reference_number") or "-",
        "fees": fee_rows,
        "total": total,
        "remarks": receipt.get("remarks") or "-",
    }


def generate_receipt_pdf(receipt, student, fees):
    """Returns a BytesIO holding a one-page A4 PDF receipt."""
    d = build_receipt_data(receipt, student, fees)
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Fee Receipt {d['receipt_no']}")
    c.setAuthor(CENTRE["name"])
    _, H = A4
    draw_receipt(c, d, H - 20 * mm)
    c.save()
    buffer.seek(0)
    return buffer
