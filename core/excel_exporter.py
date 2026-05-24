# core/excel_exporter.py
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


HEADERS = [
    "#",
    "Status",
    "Priority",
    "Task Description",
    "Category",
    "Deadline",
    "Entry Date",
    "Memo",
]

STATUS_DONE_VALUES = {"[x]", "[done]", "done", "✅"}


def _normalize_cell(value):
    if value is None:
        return ""
    return str(value).strip()


def _display_status(status):
    clean_status = _normalize_cell(status)
    if clean_status.lower() in STATUS_DONE_VALUES:
        return "Done"
    if clean_status:
        return "Open"
    return ""


def export_tasks_to_excel(tasks, output_path, sheet_name="NoBrainFog Tasks"):
    """
    Write NoBrainFog task dictionaries to an .xlsx workbook.

    Args:
        tasks: Iterable of task dictionaries from TodoHandler.get_tasks().
        output_path: Target .xlsx path.
        sheet_name: Excel worksheet name.

    Returns:
        pathlib.Path for the generated workbook.
    """
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name[:31]

    worksheet.append(HEADERS)

    header_fill = PatternFill("solid", fgColor="D9EAD3")
    header_font = Font(bold=True)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment

    for task in tasks:
        worksheet.append([
            task.get("number", ""),
            _display_status(task.get("status", "")),
            _normalize_cell(task.get("priority", "")),
            _normalize_cell(task.get("task", "")),
            _normalize_cell(task.get("category", "")),
            _normalize_cell(task.get("deadline", "")),
            _normalize_cell(task.get("entry_date", "")),
            _normalize_cell(task.get("memo", "")),
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    column_widths = {
        "A": 6,
        "B": 12,
        "C": 12,
        "D": 48,
        "E": 18,
        "F": 16,
        "G": 16,
        "H": 48,
    }

    for column_letter, width in column_widths.items():
        worksheet.column_dimensions[column_letter].width = width

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    for row_index in range(2, worksheet.max_row + 1):
        worksheet.row_dimensions[row_index].height = 32

    workbook.save(output)
    return output
