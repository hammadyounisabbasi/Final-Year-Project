"""Safe extraction and professional exports for temporary exam-assistant data."""

from __future__ import annotations

import csv
import io
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from app.services.timetable_documents import extract_document_text


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 100_000


def validate_and_extract(filename: str, content: bytes) -> tuple[str, dict]:
    """Validate a file and preserve spreadsheet row/column relationships."""
    safe_name = Path((filename or "").replace("\\", "/")).name.strip()
    suffix = Path(safe_name).suffix.lower()
    if not safe_name or suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Use a PDF, DOCX, TXT, CSV, or XLSX file")
    if not content:
        raise ValueError("The uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise OverflowError("The file exceeds the 8 MB upload limit")
    if suffix == ".pdf" and not content.startswith(b"%PDF"):
        raise ValueError("The file does not contain a valid PDF header")
    if suffix in {".docx", ".xlsx"} and not content.startswith(b"PK"):
        raise ValueError("The Office document is invalid or corrupted")

    metadata: dict = {"filename": safe_name, "extension": suffix.lstrip("."), "rows": 0, "columns": []}
    if suffix == ".csv":
        decoded = content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(decoded)))
        text, metadata = _structured_rows(safe_name, rows, metadata)
    elif suffix == ".xlsx":
        from openpyxl import load_workbook

        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        sections = []
        total_rows = 0
        column_sets = []
        for sheet in workbook.worksheets:
            rows = [["" if value is None else str(value).strip() for value in row]
                    for row in sheet.iter_rows(values_only=True)]
            sheet_text, sheet_meta = _structured_rows(safe_name, rows, dict(metadata))
            if sheet_text:
                sections.append(f"Sheet: {sheet.title}\n{sheet_text}")
                total_rows += sheet_meta["rows"]
                column_sets.extend(sheet_meta["columns"])
        workbook.close()
        text = "\n\n".join(sections)
        metadata.update(rows=total_rows, columns=list(dict.fromkeys(column_sets)))
    else:
        text = extract_document_text(safe_name, content)

    text = "\n".join(line.rstrip() for line in text.splitlines() if line.strip()).strip()
    if not text:
        raise ValueError("No readable content could be extracted")
    if len(text) > MAX_EXTRACTED_CHARACTERS:
        raise ValueError("Extracted content exceeds the 100,000 character limit")
    metadata["characters"] = len(text)
    return text, metadata


def _structured_rows(filename: str, rows: list[list[str]], metadata: dict) -> tuple[str, dict]:
    rows = [[str(cell).strip() for cell in row] for row in rows if any(str(cell).strip() for cell in row)]
    if not rows:
        return "", metadata
    headers = [cell or f"Column {index + 1}" for index, cell in enumerate(rows[0])]
    lines = [" | ".join(headers)]
    for row_number, row in enumerate(rows[1:], 2):
        cells = row + [""] * (len(headers) - len(row))
        pairs = [f"{header}: {cells[index]}" for index, header in enumerate(headers) if cells[index]]
        if pairs:
            lines.append(f"Row {row_number} | " + " | ".join(pairs))
    metadata.update(rows=max(0, len(rows) - 1), columns=headers)
    return "\n".join(lines), metadata


def build_exam_pdf(title: str, rows: list[dict], context: dict):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output = BytesIO()
    styles = getSampleStyleSheet()
    cell = ParagraphStyle("ExamCell", parent=styles["Normal"], fontSize=7, leading=9)
    story = [Paragraph("University of Haripur", styles["Title"]), Paragraph(escape(title), styles["Heading2"])]
    scope = " | ".join(str(value) for value in (context.get("department"),
                       f"Semester {context.get('semester')}" if context.get("semester") else None,
                       f"Section {context.get('section')}" if context.get("section") else None,
                       context.get("academic_year")) if value)
    if scope:
        story.extend([Paragraph(escape(scope), styles["Normal"]), Spacer(1, 10)])
    headers, keys = _export_columns(title)
    data = [[Paragraph(escape(header), cell) for header in headers]]
    data += [[Paragraph(escape(str(row.get(key, ""))), cell) for key in keys] for row in rows]
    table = Table(data, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eff9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 10), Paragraph("Generated proposal — not saved or approved.", styles["Italic"])])
    document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=28)
    document.build(story, onFirstPage=_pdf_footer, onLaterPages=_pdf_footer)
    output.seek(0)
    return output


def _pdf_footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(24, 14, "Exam Scheduling Assistant")
    canvas.drawRightString(818, 14, f"Page {document.page}")
    canvas.restoreState()


def build_exam_docx(title: str, rows: list[dict], context: dict):
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt

    document = Document()
    section = document.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    heading = document.add_heading("University of Haripur", 0)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle = document.add_heading(title, 1)
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    scope = " | ".join(str(value) for value in (context.get("department"),
                       f"Semester {context.get('semester')}" if context.get("semester") else None,
                       f"Section {context.get('section')}" if context.get("section") else None,
                       context.get("academic_year")) if value)
    if scope:
        paragraph = document.add_paragraph(scope)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    headers, keys = _export_columns(title)
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        table.rows[0].cells[index].text = header
    for item in rows:
        cells = table.add_row().cells
        for index, key in enumerate(keys):
            cells[index].text = str(item.get(key, ""))
    note = document.add_paragraph("Generated proposal — not saved or approved.")
    note.runs[0].italic = True
    for paragraph in document.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Arial"
            run.font.size = Pt(9)
    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output


def _export_columns(title: str):
    if "Seating" in title:
        return (["Date", "Exam / Course", "Room", "Capacity", "Section", "Roll Number Range", "Assigned Students"],
                ["date", "exam_course", "room", "capacity", "section", "roll_number_range", "assigned_students"])
    return (["Date", "Day", "Course Code", "Course Name", "Semester / Section", "Start Time", "End Time", "Room"],
            ["date", "day", "course_code", "course_name", "semester_section", "start_time", "end_time", "room"])
