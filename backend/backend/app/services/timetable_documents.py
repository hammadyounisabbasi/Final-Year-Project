"""Read-only extraction for admin timetable references."""

from io import BytesIO
from pathlib import Path
from functools import lru_cache
from threading import Lock

_OCR_LOCK = Lock()


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def extract_document_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in ('.docx', '.xlsx'):
        from zipfile import ZipFile
        with ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > 2000 or sum(item.file_size for item in archive.infolist()) > 50*1024*1024:
                raise ValueError('Expanded document exceeds the safe processing limit')
    if suffix == ".txt":
        return content.decode("utf-8", errors="replace").strip()
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        if len(reader.pages) > 50:
            raise ValueError('References are limited to 50 pages')
        parts = []
        rendered = None
        try:
            for index, page in enumerate(reader.pages):
                text = page.extract_text(extraction_mode='layout') or ''
                if not text.strip():
                    import pymupdf
                    if rendered is None: rendered = pymupdf.open(stream=content, filetype='pdf')
                    rect = rendered[index].rect
                    if rect.width * rect.height * 4 > 16000000:
                        raise ValueError('PDF page exceeds safe OCR rendering size')
                    pix = rendered[index].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
                    text = extract_document_text('page.png', pix.tobytes('png'))
                    if not text.strip(): raise ValueError(f'No readable content on page {index+1} after OCR')
                parts.append(text)
        finally:
            if rendered is not None: rendered.close()
        return '\n'.join(parts).strip()
    if suffix == ".docx":
        from docx import Document

        document = Document(BytesIO(content))
        parts = [paragraph.text for paragraph in document.paragraphs]
        parts.extend(' | '.join(cell.text for cell in row.cells) for table in document.tables for row in table.rows)
        return '\n'.join(parts).strip()
    if suffix == '.csv':
        import csv
        import io
        rows = csv.reader(io.StringIO(content.decode('utf-8-sig', errors='replace')))
        return '\n'.join(' | '.join(cell.strip() for cell in row) for row in rows).strip()
    if suffix == '.xlsx':
        from openpyxl import load_workbook
        workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
        parts = []
        for sheet in workbook.worksheets:
            parts.append(f'Sheet: {sheet.title}')
            for row in sheet.iter_rows(values_only=True):
                values = [str(value).strip() if value is not None else '' for value in row]
                if any(values): parts.append(' | '.join(values))
        workbook.close()
        return '\n'.join(parts).strip()
    if suffix in ('.png', '.jpg', '.jpeg', '.webp'):
        from PIL import Image
        import numpy as np
        with Image.open(BytesIO(content)) as picture:
            if picture.width * picture.height > 16000000:
                raise ValueError('Image exceeds 16 megapixels')
            with _OCR_LOCK:
                result, _ = _ocr_engine()(np.asarray(picture.convert('RGB')))
        # Reconstruct rows from bounding boxes, keeping table cells together.
        lines = []
        for box, value, confidence in sorted(result or [], key=lambda item: (item[0][0][1], item[0][0][0])):
            if confidence < 0.6: continue
            y = sum(p[1] for p in box) / 4
            height = max(p[1] for p in box) - min(p[1] for p in box)
            target = next((r for r in lines if abs(r[0]-y) < max(8, height * .6)), None)
            if target is None: target = [y, []]; lines.append(target)
            target[1].append((min(p[0] for p in box), value))
        return '\n'.join(' | '.join(value for _, value in sorted(cells)) for _, cells in sorted(lines))
    raise ValueError("The uploaded timetable reference format is not supported")


def extract_reference_facts(db, text):
    """Return evidence spans and exact live matches, never filename-derived facts."""
    import re
    from app.models import Teacher, Course, Department
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    def evidence(value):
        return [line for line in lines if re.search(r'\b'+re.escape(value)+r'\b', line, re.I)]
    return {
        'teachers':[{'id':t.teacher_id,'name':f'{t.first_name} {t.last_name}','evidence':evidence(f'{t.first_name} {t.last_name}')}
                    for t in db.query(Teacher).filter_by(status='Active') if evidence(f'{t.first_name} {t.last_name}')],
        'courses':[{'id':c.course_id,'name':c.course_title,'code':c.course_code,'database_credit_hours':c.credit_hours,
                    'evidence':evidence(c.course_title) or evidence(c.course_code)} for c in db.query(Course).filter_by(status='Active')
                    if evidence(c.course_title) or evidence(c.course_code)],
        'departments':[{'id':d.department_id,'name':d.department_name} for d in db.query(Department)
                       if evidence(d.department_name) or evidence(d.department_code)],
        'credit_hours':re.findall(r'\b(\d+)\s*(?:CH|credit hours?)\b',text,re.I),
        'semesters':re.findall(r'\bsemester\s+(\d+)\b',text,re.I),
        'sections':re.findall(r'\bsection\s+([\w-]+)',text,re.I),
        'capability_evidence':[line for line in lines if re.search(r'\b(teach|teaches|capable|expertise|specialization)\b',line,re.I)],
        'note':'Extracted text is shown in full for review. Unknown names remain text; uploaded capability claims do not modify database assignments.'}


def build_timetable_pdf(schedules):
    """Text-based weekly grids with separate cohort and teacher pages."""
    from collections import defaultdict
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    styles = getSampleStyleSheet()
    cell = ParagraphStyle('TimetableCell', parent=styles['Normal'], fontSize=7, leading=9)
    groups, teachers = defaultdict(list), defaultdict(list)
    for row in schedules:
        groups[(row.get('department',''),row.get('semester',''),row.get('section',''),row.get('academic_year',''))].append(row)
        teachers[(row.get('teacher','Unassigned'),row.get('academic_year',''))].append(row)
    output, story = BytesIO(), []
    general_preview = bool(schedules) and all(str(row.get('academic_year', '')).casefold() == 'general/test' for row in schedules)
    def paragraph(value): return Paragraph(escape(str(value)),cell)
    def page(title, rows):
        if story: story.append(PageBreak())
        notice = 'Read-only General/Test timetable - not connected to university records' if general_preview else 'Proposed timetable - requires administrator approval'
        story.extend([Paragraph('University of Haripur',styles['Title']),Paragraph('University Timetable Preview',styles['Heading2']),Paragraph(escape(title),styles['Heading2']),
                      Paragraph(notice,styles['Normal']),Spacer(1,12)])
        days = [d for d in ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') if any(r.get('day',r.get('day_of_week')) == d for r in rows)]
        slots = sorted({(r.get('start_time',''),r.get('end_time','')) for r in rows})
        grid = [[paragraph('Time')]+[paragraph(d) for d in days]]
        for start,end in slots:
            cells = [paragraph(f'{start} - {end}')]
            for day in days:
                selected = [r for r in rows if r.get('day',r.get('day_of_week')) == day and r.get('start_time') == start and r.get('end_time') == end]
                parts = []
                for r in selected:
                    parts.append('<br/>'.join(escape(str(v)) for v in [f"{r.get('course_code','')} - {r.get('course_title','')}",
                        f"{r.get('credit_hours','')} CH | {r.get('teacher','')}",r.get('room',r.get('room_location','')),
                        f"{r.get('department','')} | Sem {r.get('semester','')} / {r.get('section','')}"]))
                cells.append(Paragraph('<br/><br/>'.join(parts) or '-',cell))
            grid.append(cells)
        table = Table(grid,colWidths=[70]+[690/max(1,len(days))]*len(days),repeatRows=1,hAlign='LEFT',splitInRow=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eff9')),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd5e1')),
                                   ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story.append(table)
    for (department,semester,section,year),rows in groups.items(): page(f'{department} | Semester {semester} | Section {section} | {year}',rows)
    for (teacher,year),rows in teachers.items(): page(f'Teacher: {teacher} | {year}',rows)
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawRightString(805,18,f'Page {doc.page}')
    SimpleDocTemplate(output,pagesize=landscape(A4),leftMargin=35,rightMargin=35,topMargin=25,bottomMargin=30).build(story,onFirstPage=footer,onLaterPages=footer)
    output.seek(0)
    return output
