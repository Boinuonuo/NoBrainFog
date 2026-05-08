import datetime
import os
import base64
import openai
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class BrainFogProcessor:
    def __init__(self, config):
        self.driver = config.get("AI_DRIVER", "openai").strip().lower()
        self.categories = config.get("CATEGORIES")
        
        if self.driver == "gemini":
            genai.configure(api_key=config.get("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel(config.get("GEMINI_MODEL", "gemini-1.5-flash"))
        else:
            self.client = openai.OpenAI(
                api_key=config.get("API_KEY"),
                base_url=config.get("API_BASE")
            )
            self.model_name = config.get("MODEL_NAME")

    def _build_system_prompt(self, reference_task=None):
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d, %A')

        lang_instruction = "TASK and MEMO must use the same language as the current user input. Do not mix languages."
        if reference_task:
            lang_instruction = (
        f"Use this reference ONLY to infer the output language: '{reference_task}'. "
        "Do NOT copy, reuse, summarize, or transform the reference task. "
        "The new row must be based ONLY on the current user input and current image."
    )

        return f"""
        Role: 'NoBrainFog' Task Architect.
        Context: Today is {timestamp}.
        Language Policy: {lang_instruction}
        Goal: Convert user input into ONE Markdown table row.
        Categories: {self.categories}
        
        Output Format:
        | [ ] | PRIORITY | TASK | CATEGORY | DEADLINE | ENTRY_DATE | MEMO |
        
        Rules:
        1. Priority: P0(Urgent/Work), P1(High/Core), P2(Normal), P3(Backlog).
        2. Calculate precise YYYY-MM-DD for relative dates (e.g., 'next Tuesday') based on {timestamp}.
        3. Output ONLY the row content. No chatter.
        4. Never use the reference task as task content. It is for language detection only.
        """

    def _normalize_openai_image(self, image_data):
        if isinstance(image_data, str):
            return image_data

        if isinstance(image_data, dict):
            mime_type = image_data.get("mime_type", "image/png")
            data = image_data.get("data")

            if isinstance(data, bytes):
                encoded = base64.b64encode(data).decode("utf-8")
                return f"data:{mime_type};base64,{encoded}"

            if isinstance(data, str):
                if data.startswith("data:"):
                    return data
                return f"data:{mime_type};base64,{data}"

        if isinstance(image_data, bytes):
            encoded = base64.b64encode(image_data).decode("utf-8")
            return f"data:image/png;base64,{encoded}"

        return image_data
        
    def clean_my_brain(self, user_input, reference_task=None, image_data=None):
        prompt = self._build_system_prompt(reference_task)
        
        try:
            if self.driver == "gemini":
                content = [prompt, user_input]
                if image_data:
                    content.append(image_data)

                response = self.model.generate_content(content)
                return response.text.strip()

            else:
                if image_data:
                    image_url = self._normalize_openai_image(image_data)
                    user_content = [
                        {"type": "text", "text": user_input},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                else:
                    user_content = user_input

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            error_msg = f"AI API Error in clean_my_brain: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Return a safe fallback response
            fallback_task = f"| [ ] | P2 | {user_input[:100]} | Life | | | AI processing failed |"
            return fallback_task
            
    def analyze_todo(self, todo_text, mode="prior", target_task=None):
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d, %A')

        if mode == "prior":
            prompt = f"""
            Role: NoBrainFog Priority Strategist.
            Context: Today is {timestamp}.

            Analyze the following todo.md and give a practical priority report.

            Output in Chinese unless the todo content is mostly English.

            Required sections:
            1. 现在最该先做什么
            2. 今天最多做哪 3 件
            3. 哪些可以延后
            4. 哪个任务最容易卡住，以及如何降低阻力
            5. 一个非常具体的下一步动作

            Be practical, not verbose. Do not modify the todo.
            """

        elif mode == "cbt":
            prompt = f"""
            Role: NoBrainFog Cognitive Breakdown Toolkit.

            Target task:
            {target_task}

            Context: Today is {timestamp}.

            Please break down this task in a CBT-inspired but non-clinical way.
            This is productivity support, not therapy.

            Output in Chinese unless the target task is mostly English.

            Required sections:
            1. 这个任务真正要完成什么
            2. 可能卡住的心理/执行阻力
            3. 最小第一步
            4. 15 分钟版本
            5. 完整执行步骤
            6. 如果今天状态很差，最低限度怎么做
            7. 完成后会带来什么好处

            Be concrete and supportive.
            """

        elif mode == "cbt_all":
            prompt = f"""
            Role: NoBrainFog Global Execution Planner.
            Context: Today is {timestamp}.

            Analyze the whole todo.md and create a practical execution plan.

            Output in Chinese unless the todo content is mostly English.

            Required sections:
            1. 全局任务概况
            2. 今天建议处理的任务
            3. 每个重点任务的最小第一步
            4. 哪些任务可以延后
            5. 如果脑雾很重，最低限度行动清单
            6. 一句不油腻的鼓励

            Be clear, structured, and realistic.
            """

        elif mode == "yesucan":
            prompt = f"""
            Role: NoBrainFog Motivation Companion.
            Context: Today is {timestamp}.

            Read the todo.md and help the user regain momentum.

            Output in Chinese unless the todo content is mostly English.

            Required sections:
            1. 你现在不是做不到，只是入口太多
            2. 最适合先做的一个小任务
            3. 为什么这个任务值得做
            4. 怎么把它缩小到 5 分钟
            5. 完成后你会获得什么正反馈
            6. 给用户一段真诚但不油腻的鼓励

            Be warm, direct, and energizing. No fake corporate pep talk.
            """

        else:
            prompt = "Analyze the todo.md and provide a helpful plan."

        user_content = todo_text
        if target_task:
            user_content += f"\n\nTarget task:\n{target_task}"

        try:
            if self.driver == "gemini":
                response = self.model.generate_content([prompt, user_content])
                return response.text.strip()

            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.4
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            error_msg = f"AI API Error in analyze_todo (mode: {mode}): {str(e)}"
            print(f"❌ {error_msg}")
            
            # Return a safe fallback response based on mode
            fallback_responses = {
                "prior": "❌ AI analysis failed. Please check your internet connection and try again.",
                "cbt": "❌ Task breakdown failed. Please try again later.",
                "cbt_all": "❌ Global planning failed. Please try again later.",
                "yesucan": "❌ Motivation analysis failed. You can do this! Please try again later."
            }
            
            return fallback_responses.get(mode, "❌ AI analysis failed. Please try again later.")
