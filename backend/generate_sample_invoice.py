"""
generate_sample_invoice.py
──────────────────────────
Generates a realistic Indian GST Tax Invoice as a PDF.

Seller: Raj Enterprises Pvt Ltd  — GSTIN 27ABCDE1234F1Z5 (Maharashtra)
Buyer:  Priya Imports Pvt Ltd    — GSTIN 07XYZPQ9876G2Z3 (Delhi)
Supply type: Inter-state → IGST @ 18%

Run: python generate_sample_invoice.py
Output: sample_invoice.pdf  (in the backend folder)
"""

from fpdf import FPDF
from datetime import date


class InvoicePDF(FPDF):
    def header(self):
        pass  # Custom header drawn in body

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "This is a computer-generated invoice. No signature required.", align="C")


def draw_invoice():
    pdf = InvoicePDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    W = 190  # usable width (210 - 2*10 margins)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)

    # ── Header bar ──────────────────────────────────────────────
    pdf.set_fill_color(30, 58, 138)   # deep blue
    pdf.rect(10, 10, W, 22, "F")

    pdf.set_xy(10, 13)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(W / 2, 8, "TAX INVOICE", align="L")

    pdf.set_xy(W / 2 + 10, 13)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(W / 2, 4, "Invoice No: INV-2024-0042", align="R")
    pdf.set_xy(W / 2 + 10, 19)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(W / 2, 4, f"Date: {date(2024, 3, 15).strftime('%d-%b-%Y')}", align="R")

    # ── Seller + Buyer boxes ─────────────────────────────────────
    pdf.set_text_color(0, 0, 0)
    TOP = 38

    # Seller box
    pdf.set_fill_color(240, 244, 255)
    pdf.rect(10, TOP, 90, 50, "F")
    pdf.set_xy(12, TOP + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(86, 5, "SELLER", align="L")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(12, TOP + 8)
    pdf.cell(86, 5, "Raj Enterprises Pvt Ltd")

    pdf.set_font("Helvetica", "", 8.5)
    for i, line in enumerate([
        "12, MG Road, Andheri East",
        "Mumbai, Maharashtra - 400069",
        "GSTIN: 27ABCDE1234F1Z5",
        "PAN:   ABCDE1234F",
        "Email: raj@rajenterprises.in",
        "Phone: +91 98765 43210",
    ]):
        pdf.set_xy(12, TOP + 14 + i * 5)
        pdf.cell(86, 5, line)

    # Buyer box
    pdf.set_fill_color(240, 255, 244)
    pdf.rect(110, TOP, 90, 50, "F")
    pdf.set_xy(112, TOP + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(22, 101, 52)
    pdf.cell(86, 5, "BILL TO", align="L")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(112, TOP + 8)
    pdf.cell(86, 5, "Priya Imports Pvt Ltd")

    pdf.set_font("Helvetica", "", 8.5)
    for i, line in enumerate([
        "45, Connaught Place, Block C",
        "New Delhi, Delhi - 110001",
        "GSTIN: 07XYZPQ9876G2Z3",
        "PAN:   XYZPQ9876G",
        "Email: priya@priyaimports.in",
        "Phone: +91 91234 56789",
    ]):
        pdf.set_xy(112, TOP + 14 + i * 5)
        pdf.cell(86, 5, line)

    # ── Supply details ───────────────────────────────────────────
    DETAIL_Y = TOP + 55
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_xy(10, DETAIL_Y)
    pdf.cell(60, 5, f"Place of Supply: Delhi (07)")
    pdf.set_xy(80, DETAIL_Y)
    pdf.cell(60, 5, "Supply Type: Inter-State (IGST)")
    pdf.set_xy(150, DETAIL_Y)
    pdf.cell(50, 5, f"Due Date: 14-Apr-2024", align="R")

    # ── Line items table ─────────────────────────────────────────
    TABLE_Y = DETAIL_Y + 10
    COL = [10, 65, 20, 18, 20, 13, 13, 24]  # x positions
    # Headers
    pdf.set_fill_color(30, 58, 138)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(10, TABLE_Y)
    pdf.rect(10, TABLE_Y, W, 7, "F")

    headers = ["#", "Description", "HSN", "Qty", "Unit Price", "Rate%", "IGST", "Amount"]
    widths  = [7,   70,            15,    12,   25,          12,    18,    31]
    x = 10
    for h, w in zip(headers, widths):
        pdf.set_xy(x, TABLE_Y + 1)
        pdf.cell(w, 5, h, align="C")
        x += w

    # Items data
    items = [
        ("1", "Industrial Grade Laptop - 15.6\" FHD\n(Core i7, 16GB RAM, 512GB SSD)",
         "8471 30", "5", "22,000.00", "18%", "19,800.00", "1,29,800.00"),
        ("2", "Wireless Keyboard & Mouse Combo\n(USB Dongle, Ergonomic Design)",
         "8471 60", "10", "1,500.00", "18%", "2,700.00", "17,700.00"),
        ("3", "27\" 4K Monitor\n(IPS Panel, HDMI + DisplayPort)",
         "8528 52", "3", "18,000.00", "18%", "9,720.00", "63,720.00"),
        ("4", "Network Switch 24-Port Gigabit\n(Managed, Rack Mountable)",
         "8517 62", "2", "12,500.00", "18%", "4,500.00", "29,500.00"),
    ]

    pdf.set_text_color(0, 0, 0)
    row_y = TABLE_Y + 7
    for idx, (num, desc, hsn, qty, price, rate, igst, total) in enumerate(items):
        fill = idx % 2 == 0
        if fill:
            pdf.set_fill_color(248, 250, 255)
            pdf.rect(10, row_y, W, 11, "F")

        pdf.set_font("Helvetica", "", 8)
        row_data = [num, desc.split("\n")[0], hsn, qty, price, rate, igst, total]
        x = 10
        for val, w in zip(row_data, widths):
            pdf.set_xy(x, row_y + 1)
            pdf.cell(w, 5, val, align="C" if val not in [desc.split("\n")[0]] else "L")
            x += w

        # Sub-description line
        pdf.set_font("Helvetica", "I", 7.5)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(17, row_y + 6)
        pdf.cell(60, 4, desc.split("\n")[1] if "\n" in desc else "")
        pdf.set_text_color(0, 0, 0)
        row_y += 11

    # Table bottom line
    pdf.set_draw_color(30, 58, 138)
    pdf.set_line_width(0.5)
    pdf.line(10, row_y, 200, row_y)

    # ── Totals ───────────────────────────────────────────────────
    TOT_Y = row_y + 3
    pdf.set_font("Helvetica", "", 9)

    totals = [
        ("Subtotal (Taxable Value)", "2,03,000.00"),
        ("IGST @ 18%",           "36,540.00"),
        ("Cess",                 "0.00"),
        ("Round Off",            "-0.00"),
    ]
    for label, val in totals:
        pdf.set_xy(130, TOT_Y)
        pdf.cell(50, 6, label, align="R")
        pdf.set_xy(180, TOT_Y)
        pdf.cell(20, 6, f"Rs. {val}", align="R")
        TOT_Y += 6

    # Grand total
    pdf.set_fill_color(30, 58, 138)
    pdf.rect(128, TOT_Y, 72, 8, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(130, TOT_Y + 1)
    pdf.cell(50, 6, "GRAND TOTAL", align="R")
    pdf.set_xy(180, TOT_Y + 1)
    pdf.cell(20, 6, "Rs. 2,39,540.00", align="R")

    TOT_Y += 12
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_xy(10, TOT_Y)
    pdf.cell(W, 5, "Amount in Words: Two Lakh Thirty-Nine Thousand Five Hundred and Forty Rupees Only")

    # ── Bank details ─────────────────────────────────────────────
    BANK_Y = TOT_Y + 8
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(10, BANK_Y, 85, 28, "F")
    pdf.set_xy(12, BANK_Y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(81, 5, "BANK DETAILS")
    pdf.set_font("Helvetica", "", 8)
    for i, line in enumerate([
        "Bank:    HDFC Bank Ltd",
        "A/C No:  5020 0123 4567 89",
        "IFSC:    HDFC0001234",
        "Branch:  Andheri East, Mumbai",
    ]):
        pdf.set_xy(12, BANK_Y + 8 + i * 5)
        pdf.cell(81, 4, line)

    # Terms
    pdf.set_xy(110, BANK_Y + 2)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(90, 5, "TERMS & CONDITIONS")
    pdf.set_font("Helvetica", "", 7.5)
    for i, line in enumerate([
        "1. Payment due within 30 days of invoice date.",
        "2. Goods once sold will not be taken back.",
        "3. Subject to Mumbai jurisdiction.",
        "4. E&OE - Errors and Omissions Excepted.",
    ]):
        pdf.set_xy(110, BANK_Y + 8 + i * 5)
        pdf.cell(90, 4, line)

    # Signature
    SIG_Y = BANK_Y + 32
    pdf.set_xy(130, SIG_Y)
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(70, 5, "Authorised Signatory", align="C")
    pdf.set_xy(130, SIG_Y + 5)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(70, 5, "Raj Enterprises Pvt Ltd", align="C")

    pdf.output("sample_invoice.pdf")
    print("sample_invoice.pdf created successfully!")


if __name__ == "__main__":
    draw_invoice()
