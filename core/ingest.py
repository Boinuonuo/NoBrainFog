from core.processor import BrainFogProcessor
from core.handler import TodoHandler


class IngestService:
    def __init__(self, config):
        self.config = config
        self.processor = BrainFogProcessor(config)
        self.handler = TodoHandler(config.get("MD_PATH", "./todo.md"))

    def capture_task(self, text, image_data=None, source="unknown"):
        text = (text or "").strip()

        if not text and not image_data:
            raise ValueError("No text or image data provided.")

        ref = self.handler.get_first_entry_desc()

        user_input = text or "请从这张图片里整理出一个任务。"

        row = self.processor.clean_my_brain(
            user_input=user_input,
            reference_task=ref,
            image_data=image_data
        )

        saved = self.handler.add_row(row)
        if not saved:
            raise ValueError("No valid task row was generated.")

        return row

    def export_todo_path(self):
        self.handler._initialize_storage()
        return self.handler.file_path

    def cbt_all(self):
        todo_text = self.handler.get_todo_text()
        return self.processor.analyze_todo(todo_text, mode="cbt_all")
