import discord

from core.help_text import DISCORD_HELP_EMBED, DISCORD_HELP_TEXT
from core.ingest import IngestService


class NoBrainFogBot(discord.Client):
    def __init__(self, config):
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
        if message.author.bot:
            return
        if message.author.id != self.target_id:
            return
        if not isinstance(message.channel, discord.DMChannel):
            return
        if not message.content.strip() and not message.attachments:
            return

        raw_command = message.content.strip()
        command = raw_command.lower()

        if command in ["/admhelp", "/help", "/h"]:
            await self._send_help(message)
            return

        if command in ["/export", "/exp"]:
            self.handler._initialize_storage()
            await message.channel.send(
                content="Here is your NoBrainFog todo.md:",
                file=discord.File(self.handler.file_path, filename="todo.md"),
            )
            return

        if command == "/import":
            await self._handle_import(message)
            return

        if command in ["/report", "/rep"]:
            await message.channel.send(self.handler.format_report())
            return

        if command == "/undo":
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
            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/edit 2 new task text`")
                return
            ok, reply = self.handler.edit_task(parts[0], parts[1])
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
            ok, reply = self.handler.update_priority(parts[0], parts[1])
            await message.channel.send(reply)
            return

        if command.startswith("/deadline") or command.startswith("/due"):
            if command.startswith("/deadline"):
                payload = raw_command[len("/deadline"):].strip()
            else:
                payload = raw_command[len("/due"):].strip()
            parts = payload.split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/deadline 2 2026-05-30` or `/due 2 none`")
                return
            ok, reply = self.handler.update_deadline(parts[0], parts[1])
            await message.channel.send(reply)
            return

        if command.startswith("/memo"):
            parts = raw_command[len("/memo"):].strip().split(maxsplit=1)
            if len(parts) < 2:
                await message.channel.send("Usage: `/memo 2 memo text` or `/memo 2 none`")
                return
            ok, reply = self.handler.update_memo(parts[0], parts[1])
            await message.channel.send(reply)
            return

        if command in ["/prior", "/priority_report"]:
            await self._handle_analysis(message, mode="prior")
            return

        if command.startswith("/cbt"):
            await self._handle_cbt(message, raw_command)
            return

        if command in ["/yesucan", "/motivate", "/motivation"]:
            await self._handle_analysis(message, mode="yesucan")
            return

        await self._handle_capture(message)

    async def _send_help(self, message):
        embed = discord.Embed(
            title=DISCORD_HELP_EMBED["title"],
            description=DISCORD_HELP_EMBED["description"],
            color=DISCORD_HELP_EMBED.get("color", 0xBA55D3),
        )
        for field in DISCORD_HELP_EMBED["fields"]:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False),
            )
        embed.set_footer(text=DISCORD_HELP_EMBED["footer"])

        try:
            await message.channel.send(embed=embed)
        except Exception as e:
            print(f"⚠️ Failed to send Discord help embed, falling back to text: {e}")
            await message.channel.send(DISCORD_HELP_TEXT)

    async def _handle_import(self, message):
        if not message.attachments:
            await message.channel.send("Please upload a todo.md file with the `/import` command.")
            return

        md_file = None
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(".md"):
                md_file = attachment
                break

        if not md_file:
            await message.channel.send("No .md file found in attachments. Please upload a todo.md file.")
            return

        try:
            file_content = await md_file.read()
            content_str = file_content.decode("utf-8")
            success, reply = self.handler.replace_file(content_str)
            await message.channel.send(reply)
            if success:
                await message.add_reaction("✨")
        except UnicodeDecodeError:
            await message.channel.send("Failed to read the file. Please ensure it's a UTF-8 encoded text file.")
        except Exception as e:
            await message.channel.send(f"Error processing file: {e}")

    async def _handle_analysis(self, message, mode):
        await message.add_reaction("🧠")
        todo_text = self.handler.get_todo_text()
        reply = self.processor.analyze_todo(todo_text, mode=mode)
        if len(reply) > 1900:
            reply = reply[:1900] + "\n\n...Message is too long. Use /export for full todo.md."
        await message.channel.send(reply)
        await message.add_reaction("✨")

    async def _handle_cbt(self, message, raw_command):
        payload = raw_command[len("/cbt"):].strip()
        await message.add_reaction("🧠")

        if not payload:
            await message.channel.send("Usage: `/cbt 2` or `/cbt all`")
            return

        todo_text = self.handler.get_todo_text()
        if payload.lower() == "all":
            reply = self.processor.analyze_todo(todo_text, mode="cbt_all")
        else:
            task, error = self.handler._find_task(payload)
            if not task:
                await message.channel.send(error)
                return
            target_task = (
                f"#{task['number']} [{task['priority']}][{task['category']}] {task['task']}\n"
                f"Deadline: {task['deadline'] or 'No deadline'}\n"
                f"Memo: {task['memo'] or 'No memo'}"
            )
            reply = self.processor.analyze_todo(todo_text, mode="cbt", target_task=target_task)

        if len(reply) > 1900:
            reply = reply[:1900] + "\n\n...Report is too long. Try a smaller target."
        await message.channel.send(reply)
        await message.add_reaction("✨")

    async def _handle_capture(self, message):
        await message.add_reaction("🧠")
        try:
            image_data = None
            for attachment in message.attachments:
                content_type = attachment.content_type or ""
                filename = attachment.filename.lower()
                is_image = content_type.startswith("image/") or filename.endswith(
                    (".png", ".jpg", ".jpeg", ".webp", ".gif")
                )
                if is_image:
                    image_bytes = await attachment.read()
                    image_data = {
                        "mime_type": content_type or "image/png",
                        "data": image_bytes,
                    }
                    break

            if message.attachments and image_data is None:
                await message.channel.send("I found an attachment, but it was not recognized as an image.")
                return

            user_input = message.content.strip() or "请从这张图片里整理出一个任务。"
            self.ingest.capture_task(text=user_input, image_data=image_data, source="discord")
            await message.add_reaction("✨")
        except Exception as e:
            print(f"❌ Execution Error: {e}")
            await message.channel.send(f"Status: Brain Fog thickens. Error: {e}")
