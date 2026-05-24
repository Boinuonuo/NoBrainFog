#!/usr/bin/env python3
"""
NoBrainFog command-line toolkit.

Examples:
    python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env help
    python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env report
    python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env add "Check the insurance bill"
    python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env excel --output /tmp/todo.xlsx
    python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env lint
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.excel_exporter import export_tasks_to_excel
from core.handler import TodoHandler
from core.ingest import IngestService

CLI_HELP_TEXT = """
🧠 NoBrainFog CLI Toolkit

Purpose:
  Local command-line access to the same todo.md used by Discord and WeChat Work.
  Good for server shell, cron jobs, quick maintenance, and one-off exports.

Base command:
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env <command>

Config:
  Required for all commands:
    MD_PATH=/root/nbf-vault/todo.md

  Required only for AI commands:
    AI_DRIVER=openai or gemini
    API_KEY=...              # openai-compatible driver
    GEMINI_API_KEY=...       # gemini driver

Capture:
  add "task text"
    Capture a new task through the AI pipeline.
    Requires AI credentials.

    Example:
      python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env add "Check the insurance bill"

View:
  report
    Print the current NoBrainFog task report.

    Example:
      python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env report

Edit:
  done <number-or-keyword>
    Mark a task as done.

  edit <number-or-keyword> "new task text"
    Edit the task description.

  undo
    Remove the last task row.

Metadata:
  pri <number-or-keyword> P0|P1|P2|P3
    Update priority.

  due <number-or-keyword> YYYY-MM-DD
    Update deadline.

  due <number-or-keyword> none
    Clear deadline.

  memo <number-or-keyword> "memo text"
    Update memo.

  memo <number-or-keyword> none
    Clear memo.

Export & Check:
  excel --output /tmp/nobrainfog-todo.xlsx
    Export todo.md to a formatted Excel workbook.

  lint
    Compile and run the optional C todo.md table linter.
    Requires gcc.

Examples:
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env report
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env done 2
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env pri 2 P0
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env due 2 2026-05-30
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env excel --output /tmp/todo.xlsx
  python tools/nbf_cli.py --env-file /root/nobrainfog-config/cli.env lint
""".strip()


def load_env_file(env_file):
    env_path = Path(env_file).expanduser().resolve()

    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_path}")

    if not env_path.is_file():
        raise ValueError(f"Env path is not a file: {env_path}")

    load_dotenv(dotenv_path=env_path, override=True)
    return env_path


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env variable: {name}")
    return value


def build_config():
    md_path = require_env("MD_PATH")
    return {
        "AI_DRIVER": os.getenv("AI_DRIVER"),
        "API_KEY": os.getenv("API_KEY"),
        "API_BASE": os.getenv("API_BASE"),
        "MODEL_NAME": os.getenv("MODEL_NAME"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL"),
        "MD_PATH": md_path,
        "CATEGORIES": os.getenv("CATEGORIES", "Work,Life"),
    }


def require_ai_config(config):
    driver = (config.get("AI_DRIVER") or "").strip().lower()

    if driver == "openai":
        if not config.get("API_KEY"):
            raise ValueError("AI_DRIVER=openai requires API_KEY.")
        return

    if driver == "gemini":
        if not config.get("GEMINI_API_KEY"):
            raise ValueError("AI_DRIVER=gemini requires GEMINI_API_KEY.")
        return

    raise ValueError("AI_DRIVER must be 'openai' or 'gemini' for commands that use AI.")


def get_handler(config):
    return TodoHandler(config["MD_PATH"])


def join_words(words):
    return " ".join(words).strip()


def command_help(args, config):
    print(CLI_HELP_TEXT)
    return 0


def command_add(args, config):
    text = join_words(args.text)
    if not text:
        raise ValueError("Please provide task text.")

    require_ai_config(config)
    ingest = IngestService(config)
    row = ingest.capture_task(text=text, source="cli")

    print("✅ Added task to NoBrainFog")
    print(row)
    return 0


def command_report(args, config):
    handler = get_handler(config)
    print(handler.format_report())
    return 0


def command_excel(args, config):
    handler = get_handler(config)
    output_path = Path(args.output).expanduser().resolve()
    tasks = handler.get_tasks()
    generated_path = export_tasks_to_excel(tasks, output_path)

    print("✅ Exported NoBrainFog tasks to Excel")
    print(f"Output: {generated_path}")
    print(f"Tasks:  {len(tasks)}")
    return 0


def command_lint(args, config):
    gcc_path = shutil.which("gcc")
    if not gcc_path:
        raise RuntimeError("gcc was not found. Install gcc or run the C lint tool manually on a machine with gcc.")

    source_path = PROJECT_ROOT / "tools" / "c" / "nbf-todo-lint.c"
    if not source_path.exists():
        raise FileNotFoundError(f"C lint source not found: {source_path}")

    md_path = Path(config["MD_PATH"]).expanduser().resolve()
    if not md_path.exists():
        raise FileNotFoundError(f"todo.md not found: {md_path}")

    with tempfile.TemporaryDirectory(prefix="nbf-cli-") as temp_dir:
        binary_path = Path(temp_dir) / "nbf-todo-lint"

        compile_result = subprocess.run(
            [gcc_path, str(source_path), "-o", str(binary_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if compile_result.returncode != 0:
            print(compile_result.stdout, end="")
            print(compile_result.stderr, end="", file=sys.stderr)
            return compile_result.returncode

        lint_result = subprocess.run(
            [str(binary_path), str(md_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        print(lint_result.stdout, end="")
        print(lint_result.stderr, end="", file=sys.stderr)
        return lint_result.returncode


def command_done(args, config):
    ok, reply = get_handler(config).mark_done(args.selector)
    print(reply)
    return 0 if ok else 1


def command_edit(args, config):
    ok, reply = get_handler(config).edit_task(args.selector, join_words(args.new_text))
    print(reply)
    return 0 if ok else 1


def command_priority(args, config):
    ok, reply = get_handler(config).update_priority(args.selector, args.priority)
    print(reply)
    return 0 if ok else 1


def command_deadline(args, config):
    ok, reply = get_handler(config).update_deadline(args.selector, args.deadline)
    print(reply)
    return 0 if ok else 1


def command_memo(args, config):
    ok, reply = get_handler(config).update_memo(args.selector, join_words(args.memo))
    print(reply)
    return 0 if ok else 1


def command_undo(args, config):
    ok, reply = get_handler(config).undo_last()
    print(reply)
    return 0 if ok else 1


def build_parser():
    parser = argparse.ArgumentParser(
        description="NoBrainFog command-line toolkit for todo.md operations."
    )
    parser.add_argument(
        "--env-file",
        required=True,
        help="Path to an env file containing at least MD_PATH. AI commands also need AI config.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    help_parser = subparsers.add_parser("help", help="Show the NoBrainFog CLI toolkit manual.")
    help_parser.set_defaults(func=command_help)

    add_parser = subparsers.add_parser("add", help="Capture a new task through the AI pipeline.")
    add_parser.add_argument("text", nargs="+", help="Task text to capture.")
    add_parser.set_defaults(func=command_add)

    report_parser = subparsers.add_parser("report", help="Print the current task report.")
    report_parser.set_defaults(func=command_report)

    excel_parser = subparsers.add_parser("excel", help="Export todo.md to a formatted Excel workbook.")
    excel_parser.add_argument("--output", required=True, help="Output .xlsx path.")
    excel_parser.set_defaults(func=command_excel)

    lint_parser = subparsers.add_parser("lint", help="Compile and run the optional C todo.md linter.")
    lint_parser.set_defaults(func=command_lint)

    done_parser = subparsers.add_parser("done", help="Mark a task done by number or keyword.")
    done_parser.add_argument("selector", help="Task number or keyword.")
    done_parser.set_defaults(func=command_done)

    edit_parser = subparsers.add_parser("edit", help="Edit a task description by number or keyword.")
    edit_parser.add_argument("selector", help="Task number or keyword.")
    edit_parser.add_argument("new_text", nargs="+", help="New task description.")
    edit_parser.set_defaults(func=command_edit)

    priority_parser = subparsers.add_parser("pri", aliases=["priority"], help="Update task priority.")
    priority_parser.add_argument("selector", help="Task number or keyword.")
    priority_parser.add_argument("priority", help="Priority: P0, P1, P2, or P3.")
    priority_parser.set_defaults(func=command_priority)

    due_parser = subparsers.add_parser("due", aliases=["deadline"], help="Update or clear task deadline.")
    due_parser.add_argument("selector", help="Task number or keyword.")
    due_parser.add_argument("deadline", help="Deadline value, or 'none' to clear.")
    due_parser.set_defaults(func=command_deadline)

    memo_parser = subparsers.add_parser("memo", help="Update or clear task memo.")
    memo_parser.add_argument("selector", help="Task number or keyword.")
    memo_parser.add_argument("memo", nargs="+", help="Memo text, or 'none' to clear.")
    memo_parser.set_defaults(func=command_memo)

    undo_parser = subparsers.add_parser("undo", help="Remove the last task row.")
    undo_parser.set_defaults(func=command_undo)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        env_path = load_env_file(args.env_file)
        config = build_config()
        if args.command not in {"report", "help"}:
            print(f"✅ Loaded env file: {env_path}")
        return args.func(args, config)
    except Exception as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
