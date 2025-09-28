import json
import os
from typing import List, Dict, Tuple, Any
import google.generativeai as genai
import ollama

# 全域定義安全設定，方便重複使用
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class ChatModule:
    """
    代表一個獨立的 AI 聊天模組（一個 AI 角色）。
    """
    def __init__(self, config_path: str):
        """
        透過載入其設定檔來初始化聊天模組。
        """
        self.config = self._load_config(config_path)
        self.module_id: str = self.config.get("module_id", "unknown_module")
        self.character_setting: str = self.config.get("character_setting", "")
        model_config = self.config.get("model", {})
        self.model_provider: str = model_config.get("provider", "gemini")
        self.model_name: str = model_config.get("name", "gemini-1.5-flash-lite")
        self.output_parser: str = self.config.get("output_parser", "default")
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """根據供應商初始化對應的 AI 客戶端。"""
        print(f"正在為模組 '{self.module_id}' 準備模型供應商 '{self.model_provider}'...")
        if self.model_provider == "gemini":
            if os.getenv("GEMINI_API_KEY"):
                print(f"  - Gemini API 金鑰已找到，將在需要時使用。")
            else:
                print(f"  - 警告：找不到 GEMINI_API_KEY。")
        elif self.model_provider == "ollama":
            try:
                host = os.getenv("OLLAMA_HOST")
                self.client = ollama.Client(host=host)
                self.client.list()
                print(f"  - Ollama 客戶端已成功設定 (主機: {host or '預設'})。")
            except Exception as e:
                print(f"  - 錯誤：設定 Ollama 時發生錯誤: {e}")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """私有方法：載入指定路徑的 JSON 設定檔。"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"錯誤：讀取或解析設定檔 {config_path} 時失敗: {e}")
            return {}

    def _construct_gemini_prompt(self, history: List[Dict[str, str]], available_modules: List[str]) -> str:
        """為 Gemini 建構一個詳細的、結構化的提示。"""
        # 分離出使用者最新的提問和過去的對話歷史
        user_task = history[-1]['content']
        conversation_history = history[:-1]

        prompt = "### 你的角色 (Your Role) ###\n"
        prompt += f"{self.character_setting}\n\n"

        prompt += "### 需要完成的任務 (Your Task) ###\n"
        prompt += f"{user_task}\n\n"

        if conversation_history:
            prompt += "### 參考對話歷史 (For Your Reference: Conversation History) ###\n"
            for turn in conversation_history:
                prompt += f"- {turn['role']}: {turn['content']}\n"
            prompt += "\n"

        prompt += "### 注意事項 (Instructions) ###\n"
        if self.output_parser == "json":
            next_module_options = [m for m in available_modules if m != self.module_id]
            prompt += "1. 根據你的角色和任務，生成你的回應內容。\n"
            prompt += f"2. 決定下一個對話模組。選項: {next_module_options}。或用 'END' 結束。\n"
            prompt += "3. **你的整個輸出必須是一個 RFC 8259 標準的 JSON 物件**，不含任何額外文字。格式如下:\n"
            prompt += '{\n  "response": "你對任務的回應。",\n  "next_module": "下一個模組的 ID"\n}'
        else:
            prompt += "請根據你的角色和任務，直接提供你的回應。"

        return prompt

    def list_available_models(self) -> List[str]:
        """列出目前 API 金鑰可用的對話模型。此功能目前僅支援 Gemini。"""
        if self.model_provider != "gemini":
            return [self.model_name]
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key: return [self.model_name]
            genai.configure(api_key=api_key)
            print("正在向 Google 查詢可用的 Gemini 模型...")
            models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print(f"找到 {len(models)} 個可用的對話模型。")
            return models if models else [self.model_name]
        except Exception as e:
            print(f"錯誤：查詢可用模型時失敗: {e}")
            return [self.model_name]

    def _build_ollama_messages(self, history: List[Dict[str, str]], available_modules: List[str]]) -> List[Dict[str, str]]:
        """將我們的歷史紀錄格式轉換為 Ollama 需要的格式。"""
        # 為 Ollama 也建立結構化的系統提示
        system_prompt = self._construct_gemini_prompt(history, available_modules)
        # 在 Ollama 中，通常將所有指令放在 system prompt 中
        return [{"role": "system", "content": system_prompt}]

    def generate_response(self, history: List[Dict[str, str]], available_modules: List[str], model_override_name: str = None) -> Tuple[str, str]:
        """生成回應。此版本會根據供應商動態呼叫 Gemini 或 Ollama。"""
        model_to_use = model_override_name if model_override_name else self.model_name
        print(f"--- 正在為 {self.module_id} (模型: {self.model_provider}/{model_to_use}) 呼叫 API ---")

        try:
            if self.model_provider == "gemini":
                prompt = self._construct_gemini_prompt(history, available_modules)
                model = genai.GenerativeModel(model_to_use, safety_settings=SAFETY_SETTINGS)
                response = model.generate_content(prompt)

                if not response.candidates:
                    return f"抱歉，Gemini請求似乎因 '{getattr(response.prompt_feedback, 'block_reason', '未知')}' 而被攔截。", "END"

                candidate = response.candidates[0]
                if candidate.finish_reason.name != "STOP":
                    return f"抱歉，AI因為 '{candidate.finish_reason.name}' 的原因提前中止了回應。", "END"

                response_text = candidate.content.parts[0].text if candidate.content and candidate.content.parts else ""

            elif self.model_provider == "ollama":
                if not self.client: return f"錯誤：Ollama 客戶端未被初始化。", "END"
                messages = self._build_ollama_messages(history, available_modules)
                response = self.client.chat(model=model_to_use, messages=messages)
                response_text = response['message']['content']

            if self.output_parser == "json":
                cleaned_text = response_text.strip().replace("```json", "").replace("```", "").strip()
                parsed_output = json.loads(cleaned_text)
                final_response = parsed_output.get("response", "錯誤：AI回傳的JSON中缺少 'response' 欄位。")
                next_module = parsed_output.get("next_module", "END")
            else:
                final_response = response_text
                next_module = "END"

        except json.JSONDecodeError:
            final_response = "抱歉，我的思緒有點混亂，無法產生正確的 JSON 格式。"
            next_module = "END"
        except Exception as e:
            print(f"錯誤：在與 {self.model_provider} API 互動時發生錯誤: {e}")
            final_response = f"抱歉，我在思考時遇到了一點問題 ({e})。"
            next_module = "END"

        return final_response, next_module