from io import BytesIO
from typing import List, Optional

from fpdf import FPDF


def generate_pdf_bytes(title: str, sections: Optional[List[dict]] = None) -> bytes:
    """Generate a simple PDF with a title and bullet sections."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title or "Report", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 12)

    if sections:
        for section in sections:
            heading = section.get("heading") or "Section"
            body = section.get("body") or ""
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 8, heading)
            pdf.set_font("Helvetica", "", 12)
            pdf.multi_cell(0, 7, body)
            pdf.ln(2)
    else:
        pdf.multi_cell(0, 7, "No content provided.")

    # Return raw bytes
    return pdf.output(dest="S").encode("latin1")


def pdf_bytesio(title: str, sections: Optional[List[dict]] = None) -> BytesIO:
    return BytesIO(generate_pdf_bytes(title, sections))

