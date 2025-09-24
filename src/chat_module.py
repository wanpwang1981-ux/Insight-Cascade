import json
import os
from typing import List, Dict, Tuple, Any
import google.generativeai as genai

class ChatModule:
    """
    代表一個獨立的 AI 聊天模組（一個 AI 角色）。
    它會從一個設定檔進行初始化，並根據其角色設定和對話歷史來生成回應。
    """
    def __init__(self, config_path: str):
        """
        透過載入其設定檔來初始化聊天模組，並設定 Gemini API。

        Args:
            config_path (str): 此模組的 JSON 設定檔路徑。
        """
        # 載入設定檔並賦值給各個屬性
        self.config = self._load_config(config_path)
        self.module_id: str = self.config.get("module_id", "unknown_module")
        self.character_setting: str = self.config.get("character_setting", "")
        self.model_endpoint: str = self.config.get("model_endpoint", "gemini-1.5-flash") # Default to a fast model
        self.output_parser = self.config.get("output_parser", "default")
        self.next_module_selector = self.config.get("next_module_selector", "end_conversation")

        # 設定 Gemini API
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_endpoint)
                print(f"模組 '{self.module_id}' 的 Gemini 模型 ({self.model_endpoint}) 已成功設定。")
            except Exception as e:
                print(f"錯誤：為模組 '{self.module_id}' 設定 Gemini 時發生錯誤: {e}")
                self.model = None
        else:
            print(f"警告：找不到 GEMINI_API_KEY。模組 '{self.module_id}' 將無法呼叫 AI。")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        私有方法：載入指定路徑的 JSON 設定檔。
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"錯誤：在 {config_path} 找不到設定檔")
            return {}
        except json.JSONDecodeError:
            print(f"錯誤：無法解析 {config_path} 的 JSON 內容")
            return {}

    def construct_prompt(self, history: List[Dict[str, str]]) -> str:
        """
        為 AI 模型建構一個詳細的提示 (Prompt)，包含角色設定和對話歷史。
        """
        prompt = f"系統提示: {self.character_setting}\n\n"
        prompt += "對話歷史:\n"
        for turn in history:
            prompt += f"- {turn['role']}: {turn['content']}\n"

        prompt += "\n你的任務: 請根據你的角色設定和以上的對話歷史，提供你的回應。"
        return prompt

    def generate_response(self, history: List[Dict[str, str]]) -> Tuple[str, str]:
        """
        生成回應。此版本會嘗試呼叫 Gemini API，如果失敗則回傳錯誤訊息。
        """
        # 建立提示
        prompt = self.construct_prompt(history)

        # 檢查模型是否已成功初始化
        if not self.model:
            error_message = "錯誤：Gemini 模型未被初始化，可能是因為缺少 API 金鑰或設定失敗。"
            return error_message, "END"

        print(f"--- 正在為 {self.module_id} 呼叫 Gemini API ({self.model_endpoint}) ---")

        try:
            # 呼叫 Gemini API
            response = self.model.generate_content(prompt)
            response_text = response.text
        except Exception as e:
            print(f"錯誤：呼叫 Gemini API 時發生錯誤: {e}")
            response_text = f"抱歉，我在思考時遇到了一點問題 ({e})。"

        # 根據設定檔中的簡單邏輯來決定下一個模組
        next_module = self.next_module_selector
        if next_module == "end_conversation":
            next_module = "END" # 使用一個標準化的關鍵字來結束對話

        return response_text, next_module
