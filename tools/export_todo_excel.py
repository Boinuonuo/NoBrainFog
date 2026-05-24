#!/usr/bin/env python3
"""
Export a NoBrainFog todo.md vault to an Excel .xlsx workbook.

Example:
    python tools/export_todo_excel.py \
        --input /root/nbf-vault/todo.md \
        --output /tmp/nobrainfog-todo.xlsx
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.excel_exporter import export_tasks_to_excel
from core.handler import TodoHandler


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export a NoBrainFog todo.md task vault to an Excel .xlsx file."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to todo.md, for example /root/nbf-vault/todo.md",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for the generated .xlsx file, for example /tmp/nobrainfog-todo.xlsx",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        print(f"❌ todo.md not found: {input_path}")
        return 1

    if not input_path.is_file():
        print(f"❌ Input path is not a file: {input_path}")
        return 1

    handler = TodoHandler(str(input_path))
    tasks = handler.get_tasks()

    generated_path = export_tasks_to_excel(tasks, output_path)

    print("✅ Exported NoBrainFog tasks to Excel")
    print(f"Input:  {input_path}")
    print(f"Output: {generated_path}")
    print(f"Tasks:  {len(tasks)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
