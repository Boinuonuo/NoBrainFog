DISCORD_HELP_TEXT = """
🧠 NoBrainFog Discord Help

基础：
/report 或 /rep
查看当前 todo 列表，带临时编号。

/export 或 /exp
导出完整 todo.md 文件。

/import
上传 todo.md 文件来替换现有任务，会自动备份原文件。

新增任务：
直接发文字、图片、或图文混合给我。
我会整理成一条 Markdown todo。
处理时会先给 🧠，成功后给 ✨。

管理任务：
/done 2
把 #2 任务标记为完成。

/done 地毯
用关键词匹配任务并标记完成；如果匹配多条，会要求你用编号。

/edit 2 新任务内容
修改 #2 的 Task Description。

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

/yesucan 或 /motivate 或 /motivation
生成一段推进/鼓励消息。

推荐工作流：
1. 直接把脑子里的碎片发给我
2. 用 /report 查看编号
3. 用 /done、/edit、/pri、/due、/memo 管理任务
4. 用 /prior 或 /cbt 处理卡住的任务
5. 用 /export 备份完整 todo.md
""".strip()


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
语音转写暂未接入。
如果 AI 响应很慢，企业微信可能重试请求；NoBrainFog 会用 MsgId 去重，避免重复写入。
""".strip()
