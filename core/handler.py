# core/handler.py
import os

class TodoHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self._initialize_storage()

    def _initialize_storage(self):
        if not os.path.exists(self.file_path):
            header = "| Status | Priority | Task Description | Category | Deadline | Entry Date | Memo |\n"
            separator = "| :---: | :--- | :--- | :--- | :---: | :---: | :--- |\n"
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("# 🧠 NoBrainFog - Task Vault\n\n")
                f.write(header)
                f.write(separator)

    def get_first_entry_desc(self):
        """
        Scans the vault for the first task description to lock the language.
        """
        if not os.path.exists(self.file_path):
            return None
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("| ["):
                    columns = line.split("|")
                    if len(columns) > 3:
                        return columns[3].strip()
        return None

    def add_row(self, row_content):
        self._initialize_storage()

        if not row_content:
            return False

        clean_row = row_content.replace("```markdown", "").replace("```", "").strip()
        if not clean_row:
            return False

        if not clean_row.startswith("|"):
            return False

        if not clean_row.endswith("\n"):
            clean_row += "\n"

        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(clean_row)

        return True

    def get_tasks(self):
        """
        Reads todo.md and returns task rows with temporary numbers.
        """
        self._initialize_storage()

        tasks = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        task_number = 1
        for line_index, line in enumerate(lines):
            clean_line = line.strip()

            if not clean_line.startswith("| ["):
                continue

            columns = line.split("|")
            if len(columns) < 8:
                continue

            task = {
                "number": task_number,
                "line_index": line_index,
                "status": columns[1].strip(),
                "priority": columns[2].strip().replace("**", ""),
                "task": columns[3].strip(),
                "category": columns[4].strip(),
                "deadline": columns[5].strip(),
                "entry_date": columns[6].strip(),
                "memo": columns[7].strip()
            }
            tasks.append(task)
            task_number += 1

        return tasks

    def format_report(self):
        """
        Formats current tasks into a Discord-friendly report.
        """
        tasks = self.get_tasks()

        if not tasks:
            return "🧠 NoBrainFog Report\n\nNo tasks found."

        lines = ["🧠 NoBrainFog Report\n"]

        for task in tasks:
            status_icon = "✅" if task["status"].lower() in ["[x]", "[done]"] else "⬜"
            deadline = task["deadline"] if task["deadline"] else "No deadline"
            memo = task["memo"] if task["memo"] else ""

            lines.append(
                f'{status_icon} #{task["number"]} '
                f'[{task["priority"]}][{task["category"]}] {task["task"]}'
            )
            lines.append(f'    Deadline: {deadline}')

            if memo:
                lines.append(f'    Memo: {memo}')

            lines.append("")

        report = "\n".join(lines).strip()

        if len(report) > 1900:
            return report[:1900] + "\n\n...Report is too long. Use /export for full todo.md."

        return report

    def get_todo_text(self):
        """
        Reads the full todo.md content for AI analysis.
        """
        self._initialize_storage()

        with open(self.file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def _find_task(self, selector):
        """
        Finds a task by temporary number or keyword.
        Returns: (task, message)
        """
        tasks = self.get_tasks()
        selector = str(selector).strip()

        if not selector:
            return None, "Please provide a task number or keyword."

        if selector.isdigit():
            number = int(selector)
            for task in tasks:
                if task["number"] == number:
                    return task, None
            return None, f"Task #{number} was not found."

        matches = []
        selector_lower = selector.lower()

        for task in tasks:
            searchable = f'{task["task"]} {task["memo"]} {task["category"]}'.lower()
            if selector_lower in searchable:
                matches.append(task)

        if not matches:
            return None, f"No task matched: {selector}"

        if len(matches) > 1:
            lines = [f"Multiple tasks matched '{selector}'. Please use the task number:\n"]
            for task in matches:
                lines.append(f'#{task["number"]} [{task["priority"]}] {task["task"]}')
            return None, "\n".join(lines)

        return matches[0], None

    def mark_done(self, selector):
        """
        Marks a task as done by number or keyword.
        """
        task, message = self._find_task(selector)
        if not task:
            return False, message

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line = lines[task["line_index"]]
        columns = line.split("|")

        if len(columns) < 8:
            return False, "The matched task row is malformed."

        columns[1] = " [x] "
        lines[task["line_index"]] = "|".join(columns)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return True, f'✅ Marked done: #{task["number"]} {task["task"]}'

    def edit_task(self, selector, new_text):
        """
        Edits the Task Description column by number or keyword.
        """
        if not new_text or not new_text.strip():
            return False, "Please provide the new task text."

        task, message = self._find_task(selector)
        if not task:
            return False, message

        safe_text = new_text.strip().replace("|", "/")

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line = lines[task["line_index"]]
        columns = line.split("|")

        if len(columns) < 8:
            return False, "The matched task row is malformed."

        old_text = columns[3].strip()
        columns[3] = f" {safe_text} "
        lines[task["line_index"]] = "|".join(columns)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return True, f'✏️ Edited #{task["number"]}: {old_text} → {safe_text}'
        
    def update_priority(self, selector, new_priority):
        """
        Updates the Priority column by number or keyword.
        """
        if not new_priority or not new_priority.strip():
            return False, "Please provide a priority: P0, P1, P2, or P3."

        priority = new_priority.strip().upper()
        if priority not in ["P0", "P1", "P2", "P3"]:
            return False, "Invalid priority. Use P0, P1, P2, or P3."

        task, message = self._find_task(selector)
        if not task:
            return False, message

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line = lines[task["line_index"]]
        columns = line.split("|")

        if len(columns) < 8:
            return False, "The matched task row is malformed."

        old_priority = columns[2].strip().replace("**", "")
        columns[2] = f" {priority} "
        lines[task["line_index"]] = "|".join(columns)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return True, f'🔥 Updated priority #{task["number"]}: {old_priority} → {priority}'

    def update_deadline(self, selector, new_deadline):
        """
        Updates the Deadline column by number or keyword.
        """
        if new_deadline is None:
            return False, "Please provide a deadline, or use `none` to clear it."

        deadline = new_deadline.strip()
        if deadline.lower() in ["none", "clear", "空", "清空", "-"]:
            deadline = ""

        task, message = self._find_task(selector)
        if not task:
            return False, message

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line = lines[task["line_index"]]
        columns = line.split("|")

        if len(columns) < 8:
            return False, "The matched task row is malformed."

        old_deadline = columns[5].strip() or "No deadline"
        new_display = deadline or "No deadline"

        safe_deadline = deadline.replace("|", "/")
        columns[5] = f" {safe_deadline} "
        lines[task["line_index"]] = "|".join(columns)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return True, f'📅 Updated deadline #{task["number"]}: {old_deadline} → {new_display}'

    def update_memo(self, selector, new_memo):
        """
        Updates the Memo column by number or keyword.
        """
        if new_memo is None:
            return False, "Please provide memo text, or use `none` to clear it."

        memo = new_memo.strip()
        if memo.lower() in ["none", "clear", "空", "清空", "-"]:
            memo = ""

        task, message = self._find_task(selector)
        if not task:
            return False, message

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        line = lines[task["line_index"]]
        columns = line.split("|")

        if len(columns) < 8:
            return False, "The matched task row is malformed."

        old_memo = columns[7].strip() or "No memo"
        new_display = memo or "No memo"

        safe_memo = memo.replace("|", "/")
        columns[7] = f" {safe_memo} "
        lines[task["line_index"]] = "|".join(columns)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return True, f'📝 Updated memo #{task["number"]}: {old_memo} → {new_display}'

    def replace_file(self, new_content):
        """
        Replaces the entire todo.md file with new content.
        Validates basic structure before replacement.
        """
        if not new_content or not new_content.strip():
            return False, "File content is empty."

        # Basic validation - check if it looks like a todo.md file
        lines = new_content.strip().split('\n')
        has_header = any('Status' in line and 'Priority' in line for line in lines)
        has_tasks = any('| [' in line for line in lines)

        if not has_header:
            return False, "Invalid format: Missing table header with Status/Priority columns."

        # Create backup before replacement
        backup_path = self.file_path + '.backup'
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    backup_content = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(backup_content)
        except Exception as e:
            return False, f"Failed to create backup: {e}"

        # Replace the file
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return True, f"✅ Successfully replaced todo.md (backup saved to {backup_path})"
        except Exception as e:
            return False, f"Failed to write file: {e}"
    
    def undo_last(self):
        """
        Removes the last task row from todo.md.
        """
        self._initialize_storage()

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        last_task_index = None

        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith("| ["):
                last_task_index = i
                break

        if last_task_index is None:
            return False, "没有可以撤回的任务。"

        removed_line = lines[last_task_index].strip()
        del lines[last_task_index]

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return True, f"↩️ 已撤回最后一条任务：\n{removed_line}"
