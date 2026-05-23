import os
import discord

from core.ingest import IngestService

class NoBrainFogBot(discord.Client):
    def __init__(self, config):
        # Using default intents and enabling message_content for DM reading
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        
        target_user_id = config.get("TARGET_USER_ID")
        if not target_user_id:
            raise ValueError("TARGET_USER_ID is missing.")

        self.target_id = int(target_user_id)
        self.ingest = IngestService(config)
        self.processor = self.ingest.processor
        self.handler = self.ingest.handler

    async def on_ready(self):
        print(f"✨ NoBrainFog Bot is now online as {self.user}")

    async def on_message(self, message):
        # Security Guard: Only process DMs from the target user
        if message.author.bot: return
        if message.author.id != self.target_id: return
        if not isinstance(message.channel, discord.DMChannel): return
        if not message.content.strip() and not message.attachments: return

        raw_command = message.content.strip()
        command = raw_command.lower()
        
        if command in ["/admhelp"]:
            help_text = """
🧠 **NoBrainFog Bot Help**

**基础**
`/report` or `/rep`
查看当前 todo 列表，带临时编号。

`/export` or `/exp`
导出完整 `todo.md` 文件。

`/import`
上传 `todo.md` 文件来替换现有任务（会自动备份原文件）。

**新增任务**
直接发文字、图片、或图文混合给我。
我会整理成一条 Markdown todo。

**完成任务**
`/done 2`
把 #2 任务标记为完成。

`/done 地毯`
用关键词匹配任务并标记完成。
如果匹配多条，会要求你用编号。

**修改任务内容**
`/edit 2 新任务内容`
修改 #2 的 Task Description。

例：
`/edit 2 物色新地砖，不买地毯了`

**修改优先级**
`/pri 2 P0`
`/priority 2 P1`

可用优先级：
`P0` 紧急
`P1` 高优先
`P2` 普通
`P3` 待办/低优先

**修改截止日期**
`/due 2 2026-05-01`
`/deadline 2 2026-05-01`

清空截止日期：
`/due 2 none`

**修改备注**
`/memo 2 记得等折扣再买`

清空备注：
`/memo 2 none`

**推荐工作流**
1. 直接把脑子里的碎片发给我
2. 用 `/report` 查看编号
3. 用 `/done`、`/edit`、`/pri`、`/due`、`/memo` 管理任务
4. 用 `/export` 备份完整 todo.md
"""
            await message.channel.send(help_text)
            return
        if command in ["/export", "/exp"]:
            self.handler._initialize_storage()

            await message.channel.send(
                content="Here is your NoBrainFog todo.md:",
                file=discord.File(self.handler.file_path, filename="todo.md")
            )
            return

        if command == "/import":
            if not message.attachments:
                await message.channel.send("Please upload a todo.md file with the `/import` command.")
                return

            # Look for .md files in attachments
            md_file = None
            for attachment in message.attachments:
                if attachment.filename.lower().endswith('.md'):
                    md_file = attachment
                    break

            if not md_file:
                await message.channel.send("No .md file found in attachments. Please upload a todo.md file.")
                return

            try:
                # Read file content
                file_content = await md_file.read()
                content_str = file_content.decode('utf-8')

                # Replace the file
                success, reply = self.handler.replace_file(content_str)
                
                await message.channel.send(reply)
                
                if success:
                    await message.add_reaction("✨")

            except UnicodeDecodeError:
                await message.channel.send("Failed to read the file. Please ensure it's a UTF-8 encoded text file.")
            except Exception as e:
                await message.channel.send(f"Error processing file: {e}")

            return

        if command in ["/report", "/rep"]:
            report = self.handler.format_report()
            await message.channel.send(report)
            return

        if command in ["/undo"]:
            ok, reply = self.handler.undo_last()
            await message.channel.send(reply)
            return
        
        if command.startswith("/done"):
            selector = raw_command[len("/done"):].strip()

            if not selector:
                await message.channel.send("Usage: `/done 2` or `/done keyword`")
                return

            ok, reply = self.handler.mark_done(selector)
            await message.channel.send(reply)
            return

        if command.startswith("/edit"):
            payload = raw_command[len("/edit"):].strip()

            if not payload:
                await message.channel.send("Usage: `/edit 2 new task text`")
                return

            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/edit 2 new task text`")
                return

            selector, new_text = parts
            ok, reply = self.handler.edit_task(selector, new_text)
            await message.channel.send(reply)
            return
        if command.startswith("/priority") or command.startswith("/pri"):
            if command.startswith("/priority"):
                payload = raw_command[len("/priority"):].strip()
            else:
                payload = raw_command[len("/pri"):].strip()

            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/priority 2 P1` or `/pri 2 P1`")
                return

            selector, new_priority = parts
            ok, reply = self.handler.update_priority(selector, new_priority)
            await message.channel.send(reply)
            return

        if command.startswith("/deadline") or command.startswith("/due"):
            if command.startswith("/deadline"):
                payload = raw_command[len("/deadline"):].strip()
            else:
                payload = raw_command[len("/due"):].strip()

            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/deadline 2 2026-05-01` or `/due 2 none`")
                return

            selector, new_deadline = parts
            ok, reply = self.handler.update_deadline(selector, new_deadline)
            await message.channel.send(reply)
            return

        if command.startswith("/memo"):
            payload = raw_command[len("/memo"):].strip()

            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/memo 2 memo text` or `/memo 2 none`")
                return

            selector, new_memo = parts
            ok, reply = self.handler.update_memo(selector, new_memo)
            await message.channel.send(reply)
            return
        if command in ["/prior", "/priority_report"]:
            await message.add_reaction("🧠")

            todo_text = self.handler.get_todo_text()
            reply = self.processor.analyze_todo(todo_text, mode="prior")

            if len(reply) > 1900:
                reply = reply[:1900] + "\n\n...Report is too long. Use /export for full todo.md."

            await message.channel.send(reply)
            await message.add_reaction("✨")
            return

        if command.startswith("/cbt"):
            payload = raw_command[len("/cbt"):].strip()

            await message.add_reaction("🧠")

            todo_text = self.handler.get_todo_text()

            if not payload:
                await message.channel.send("Usage: `/cbt 2` or `/cbt all`")
                return

            if payload.lower() == "all":
                reply = self.processor.analyze_todo(todo_text, mode="cbt_all")
            else:
                task, error = self.handler._find_task(payload)
                if not task:
                    await message.channel.send(error)
                    return

                target_task = (
                    f'#{task["number"]} '
                    f'[{task["priority"]}][{task["category"]}] '
                    f'{task["task"]}\n'
                    f'Deadline: {task["deadline"] or "No deadline"}\n'
                    f'Memo: {task["memo"] or "No memo"}'
                )

                reply = self.processor.analyze_todo(
                    todo_text,
                    mode="cbt",
                    target_task=target_task
                )

            if len(reply) > 1900:
                reply = reply[:1900] + "\n\n...Report is too long. Try a smaller target."

            await message.channel.send(reply)
            await message.add_reaction("✨")
            return

        if command in ["/yesucan", "/motivate", "/motivation"]:
            await message.add_reaction("🧠")

            todo_text = self.handler.get_todo_text()
            reply = self.processor.analyze_todo(todo_text, mode="yesucan")

            if len(reply) > 1900:
                reply = reply[:1900] + "\n\n...Message is too long. Use /prior for a shorter plan."

            await message.channel.send(reply)
            await message.add_reaction("✨")
            return
        
        
        await message.add_reaction("🧠")
        
        try:
            image_data = None
            
            for attachment in message.attachments:
                content_type = attachment.content_type or ""
                filename = attachment.filename.lower()

                is_image = (
                    content_type.startswith("image/")
                    or filename.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
                )

                if is_image:
                    image_bytes = await attachment.read()
                    image_data = {
                        "mime_type": content_type or "image/png",
                        "data": image_bytes
                    }
                    break

            if message.attachments and image_data is None:
                await message.channel.send("I found an attachment, but it was not recognized as an image.")
                return
            
            user_input = message.content.strip() or "请从这张图片里整理出一个任务。"

            self.ingest.capture_task(
                text=user_input,
                image_data=image_data,
                source="discord"
            )

            await message.add_reaction("✨")

        except Exception as e:
            print(f"❌ Execution Error: {e}")
            await message.channel.send(f"Status: Brain Fog thickens. Error: {e}")
