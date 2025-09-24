import json
import os
from typing import List, Dict, Tuple, Any
import google.generativeai as genai

class ChatModule:
    """
    代表一個獨立的 AI 聊天模組（一個 AI 角色）。
    它會從一個設定檔進行初始化，並根據其角色設定和對話歷史來生成回應。
    這個版本強化了提示工程，要求 AI 以 JSON 格式回覆以實現模組間的交棒，
    並加入了更穩健的回應處理機制。
    """
    def __init__(self, config_path: str):
        """
        透過載入其設定檔來初始化聊天模組，並設定 Gemini API。
        """
        self.config = self._load_config(config_path)
        self.module_id: str = self.config.get("module_id", "unknown_module")
        self.character_setting: str = self.config.get("character_setting", "")
        self.model_endpoint: str = self.config.get("model_endpoint", "gemini-1.5-flash")
        self.output_parser: str = self.config.get("output_parser", "default")

        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # 加入安全設定，預設不阻擋任何內容，讓我們能從程式端判斷
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
                self.model = genai.GenerativeModel(self.model_endpoint, safety_settings=safety_settings)
                print(f"模組 '{self.module_id}' 的 Gemini 模型 ({self.model_endpoint}) 已成功設定。")
            except Exception as e:
                print(f"錯誤：為模組 '{self.module_id}' 設定 Gemini 時發生錯誤: {e}")
                self.model = None
        else:
            print(f"警告：找不到 GEMINI_API_KEY。模組 '{self.module_id}' 將無法呼叫 AI。")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """私有方法：載入指定路徑的 JSON 設定檔。"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"錯誤：讀取或解析設定檔 {config_path} 時失敗: {e}")
            return {}

    def construct_prompt(self, history: List[Dict[str, str]], available_modules: List[str]) -> str:
        """
        為 AI 模型建構一個詳細的提示 (Prompt)，要求以 JSON 格式回覆。
        """
        next_module_options = [m for m in available_modules if m != self.module_id]
        prompt = f"系統提示: {self.character_setting}\n\n"
        prompt += "對話歷史:\n"
        for turn in history:
            prompt += f"- {turn['role']}: {turn['content']}\n"
        prompt += "\n--- 你的任務 ---\n"
        prompt += "1. 根據你的角色設定和對話歷史，生成你的回應內容。\n"
        prompt += f"2. 決定下一個要對話的模組是誰。可用的選項有：{next_module_options}。如果對話應該結束，請使用 'END'。\n"
        prompt += "3. **你的整個輸出必須是一個 RFC 8259 標準的 JSON 物件**，不包含任何額外的文字或解釋。格式如下:\n"
        prompt += '{\n  "response": "你想要對使用者說的話。",\n  "next_module": "下一個模組的 ID"\n}'
        return prompt

    def generate_response(self, history: List[Dict[str, str]], available_modules: List[str]) -> Tuple[str, str]:
        """
        生成回應。此版本會呼叫 Gemini API，並對回傳結果進行更詳細的檢查。
        """
        if not self.model:
            return "錯誤：Gemini 模型未被初始化。", "END"

        prompt = self.construct_prompt(history, available_modules)
        print(f"--- 正在為 {self.module_id} 呼叫 Gemini API ({self.model_endpoint}) ---")

        try:
            response = self.model.generate_content(prompt)

            # **新增的穩健性檢查**
            # 檢查是否有回傳的候選內容
            if not response.candidates:
                # 檢查 prompt_feedback 來了解原因
                feedback = response.prompt_feedback
                block_reason = getattr(feedback, 'block_reason', '未知')
                safety_ratings = getattr(feedback, 'safety_ratings', [])
                error_msg = f"API請求被拒絕，沒有生成任何內容。原因: {block_reason}。安全評級: {safety_ratings}"
                print(error_msg)
                return f"抱歉，我的請求似乎被安全機制攔截了 ({block_reason})，請您換個方式提問看看。", "END"

            # 檢查第一個候選內容的 finish_reason
            candidate = response.candidates[0]
            if candidate.finish_reason.name != "STOP":
                return f"抱歉，AI因為 '{candidate.finish_reason.name}' 的原因提前中止了回應，請再試一次。", "END"

            # 清理 AI 可能回傳的 markdown 格式
            cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

            # 解析 JSON
            parsed_output = json.loads(cleaned_response_text)
            response_text = parsed_output.get("response", "錯誤：AI回傳的JSON中缺少 'response' 欄位。")
            next_module = parsed_output.get("next_module", "END")

        except json.JSONDecodeError:
            error_msg = f"錯誤：無法解析來自 {self.module_id} 的 AI 回應。收到的內容：\n---\n{response.text}\n---"
            print(error_msg)
            response_text = "抱歉，我的思緒有點混亂，無法產生正確的回應格式。"
            next_module = "END"
        except Exception as e:
            print(f"錯誤：呼叫 Gemini API 時發生錯誤: {e}")
            response_text = f"抱歉，我在思考時遇到了一點問題 ({e})。"
            next_module = "END"

        return response_text, next_module
