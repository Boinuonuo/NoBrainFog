DISCORD_HELP_TEXT = """
🧠 NoBrainFog Discord Help

基础：
`/report` 或 `/rep`
查看当前 todo 列表，带临时编号。

`/export` 或 `/exp`
导出完整 todo.md 文件。

`/excel` 或 `/xlsx`
导出 Excel 表格文件，方便筛选、整理和归档。

`/import`
上传 todo.md 文件来替换现有任务，会自动备份原文件。

新增任务：
直接发文字、图片、或图文混合给我。
我会整理成一条 Markdown todo。
处理时会先给 🧠，成功后给 ✨。

管理任务：
`/done 2`
把 #2 任务标记为完成。

`/done 地毯`
用关键词匹配任务并标记完成；如果匹配多条，会要求你用编号。

`/edit 2 新任务内容`
修改 #2 的 Task Description。

`/pri 2 P1` 或 `/priority 2 P1`
修改优先级。可用：`P0` / `P1` / `P2` / `P3`。

`/due 2 2026-05-30` 或 `/deadline 2 2026-05-30`
修改截止日期。
清空截止日期：`/due 2 none`

`/memo 2 备注内容`
修改备注。
清空备注：`/memo 2 none`

AI 分析：
`/prior` 或 `/priority_report`
根据当前 todo.md 生成优先级建议。

`/cbt 2`
对某个任务做 CBT 拆解。

`/cbt all`
分析全部任务。

`/yesucan` 或 `/motivate` 或 `/motivation`
生成一段推进/鼓励消息。

推荐工作流：
1. 直接把脑子里的碎片发给我
2. 用 `/report` 查看编号
3. 用 `/done`、`/edit`、`/pri`、`/due`、`/memo` 管理任务
4. 用 `/prior` 或 `/cbt` 处理卡住的任务
5. 用 `/export` 备份完整 todo.md，或用 `/excel` 导出表格
""".strip()


DISCORD_HELP_EMBED = {
    "title": "🍵 NoBrainFog Command Manual 🧠",
    "description": (
        "以下是 Discord adapter 的核心指令说明。\n"
        "直接把脑子里的碎片丢给我，我会整理成结构化 `todo.md`。\n\u200b"
    ),
    "color": 0xBA55D3,
    "fields": [
        {
            "name": "📋 查看 / 导出 / 导入",
            "value": (
                "`/report` 或 `/rep`\n"
                "查看当前任务列表，带临时编号。\n"
                "*例：`/report`*\n\u200b\n"
                "`/export` 或 `/exp`\n"
                "导出完整 `todo.md` 文件。\n"
                "*例：`/export`*\n\u200b\n"
                "`/excel` 或 `/xlsx`\n"
                "导出 Excel 表格文件，方便筛选、整理和归档。\n"
                "*例：`/excel`*\n\u200b\n"
                "`/import`\n"
                "上传 `todo.md` 替换现有任务，会自动备份原文件。\n"
                "*注意：这是 Discord 独占能力。*\n\u200b"
            ),
            "inline": False,
        },
        {
            "name": "➕ 新增任务",
            "value": (
                "直接发文字、图片、或图文混合给我。\n"
                "我会整理成 Markdown todo。\n"
                "处理时会先给 🧠，成功后给 ✨。\n"
                "*例：`明天下午三点整理企业微信接口`*\n\u200b"
            ),
            "inline": False,
        },
        {
            "name": "✅ 完成与编辑",
            "value": (
                "`/done 2`\n"
                "把 `#2` 标记为完成。\n"
                "*例：`/done 2`*\n\u200b\n"
                "`/done 地毯`\n"
                "按关键词匹配任务；如果匹配多条，会要求你用编号。\n"
                "*例：`/done 地毯`*\n\u200b\n"
                "`/edit 2 新任务内容`\n"
                "修改 `#2` 的任务描述。\n"
                "*例：`/edit 2 改成研究 Cloudflare Tunnel 文档`*\n\u200b"
            ),
            "inline": False,
        },
        {
            "name": "🏷️ 优先级 / 日期 / 备注",
            "value": (
                "`/pri 2 P1` 或 `/priority 2 P1`\n"
                "修改优先级，可用 `P0` / `P1` / `P2` / `P3`。\n"
                "*例：`/pri 2 P0`*\n\u200b\n"
                "`/due 2 2026-05-30` 或 `/deadline 2 2026-05-30`\n"
                "修改截止日期。清空：`/due 2 none`\n"
                "*例：`/due 2 2026-05-30`*\n\u200b\n"
                "`/memo 2 备注内容`\n"
                "修改备注。清空：`/memo 2 none`\n"
                "*例：`/memo 2 等晚上精神好一点再做`*\n\u200b"
            ),
            "inline": False,
        },
        {
            "name": "🧠 AI 分析",
            "value": (
                "`/prior` 或 `/priority_report`\n"
                "根据当前 `todo.md` 生成优先级建议。\n"
                "*例：`/prior`*\n\u200b\n"
                "`/cbt 2`\n"
                "对某个任务做 CBT 拆解。\n"
                "*例：`/cbt 2`*\n\u200b\n"
                "`/cbt all`\n"
                "分析全部任务。\n"
                "*例：`/cbt all`*\n\u200b\n"
                "`/yesucan`、`/motivate` 或 `/motivation`\n"
                "生成一段推进/鼓励消息。\n"
                "*例：`/yesucan`*\n\u200b"
            ),
            "inline": False,
        },
        {
            "name": "✨ 推荐工作流",
            "value": (
                "1. 直接把脑子里的碎片发给我\n"
                "2. 用 `/report` 查看编号\n"
                "3. 用 `/done` / `/edit` / `/pri` / `/due` / `/memo` 管理任务\n"
                "4. 用 `/prior` 或 `/cbt` 处理卡住的任务\n"
                "5. 用 `/export` 备份 `todo.md`，或用 `/excel` 导出表格\n\u200b"
            ),
            "inline": False,
        },
    ],
    "footer": "NoBrainFog Discord Adapter | Rich UX: embeds, reactions, image input, file import/export",
}


WECHAT_HELP_TEXT = """
🧠 NoBrainFog 企业微信帮助

基础：
/report 或 /r
查看当前任务列表。

/export 或 /e
导出 todo.md 文本。长内容会自动截断。

/undo
撤回最后一条任务。

/help、/h 或 /admhelp
显示这份帮助。

新增任务：
直接发送文字，我会整理成 Markdown todo。
处理完成后会主动回复结果。

管理任务：
/done 2
把 #2 任务标记为完成。

/done 关键词
按关键词匹配任务并标记完成；如果匹配多条，会要求你用编号。

/edit 2 新任务内容
修改任务描述。

/pri 2 P1 或 /priority 2 P1
修改优先级。可用：P0 / P1 / P2 / P3。

/due 2 2026-05-30 或 /deadline 2 2026-05-30
修改截止日期。
清空截止日期：/due 2 none

/memo 2 备注内容
修改备注。
清空备注：/memo 2 none

AI 分析：
/prior 或 /priority_report
根据当前 todo.md 生成优先级建议。

/cbt 2
对某个任务做 CBT 拆解。

/cbt all
分析全部任务。

/yesucan、/motivate 或 /motivation
生成一段推进/鼓励消息。

当前限制：
/import 暂时只支持 Discord。
/excel 暂时只支持 Discord 文件发送。
语音转写暂未接入。
如果 AI 响应很慢，企业微信可能重试请求；NoBrainFog 会用 MsgId 去重，避免重复写入。
""".strip()