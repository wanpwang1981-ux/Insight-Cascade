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
    它會從一個設定檔進行初始化，並根據其角色設定和對話歷史來生成回應。
    這個版本能根據設定檔中的 'model.provider' 動態選擇使用 Gemini 或 Ollama。
    """
    def __init__(self, config_path: str):
        """
        透過載入其設定檔來初始化聊天模組，並根據供應商設定對應的 AI 客戶端。
        """
        self.config = self._load_config(config_path)
        self.module_id: str = self.config.get("module_id", "unknown_module")
        self.character_setting: str = self.config.get("character_setting", "")

        model_config = self.config.get("model", {})
        self.model_provider: str = model_config.get("provider", "gemini")
        self.model_name: str = model_config.get("name", "gemini-1.5-flash-lite")

        self.output_parser: str = self.config.get("output_parser", "default")

        # client 只為非 Gemini 的供應商在啟動時初始化
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """根據供應商初始化對應的 AI 客戶端。Gemini 的 client 將在需要時動態建立。"""
        print(f"正在為模組 '{self.module_id}' 準備模型供應商 '{self.model_provider}'...")
        if self.model_provider == "gemini":
            if not os.getenv("GEMINI_API_KEY"):
                print(f"  - 警告：找不到 GEMINI_API_KEY。")
            else:
                print(f"  - Gemini API 金鑰已找到，將在需要時使用。")

        elif self.model_provider == "ollama":
            try:
                host = os.getenv("OLLAMA_HOST")
                self.client = ollama.Client(host=host)
                self.client.list()
                print(f"  - Ollama 客戶端已成功設定 (主機: {host or '預設'})。")
            except Exception as e:
                print(f"  - 錯誤：設定 Ollama 時發生錯誤。請確認 Ollama 服務正在本機或指定的 OLLAMA_HOST 上執行。錯誤訊息: {e}")

        else:
            print(f"  - 錯誤：不支援的模型供應商 '{self.model_provider}'。")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """私有方法：載入指定路徑的 JSON 設定檔。"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"錯誤：讀取或解析設定檔 {config_path} 時失敗: {e}")
            return {}

    def construct_prompt(self, history: List[Dict[str, str]], available_modules: List[str]) -> str:
        """為 AI 模型建構一個詳細的系統提示 (System Prompt)。"""
        prompt = f"系統提示: {self.character_setting}\n\n"
        if self.output_parser == "json":
            next_module_options = [m for m in available_modules if m != self.module_id]
            prompt += "--- 你的任務 ---\n"
            prompt += "1. 根據你的角色設定和對話歷史，生成你的回應內容。\n"
            prompt += f"2. 決定下一個要對話的模組是誰。可用的選項有：{next_module_options}。如果對話應該結束，請使用 'END'。\n"
            prompt += "3. **你的整個輸出必須是一個 RFC 8259 標準的 JSON 物件**，不包含任何額外的文字或解釋。格式如下:\n"
            prompt += '{\n  "response": "你想要對使用者說的話。",\n  "next_module": "下一個模組的 ID"\n}'
        else:
            prompt += "你的任務: 請根據你的角色設定和以上的對話歷史，直接提供你的回應。"
        return prompt

    def list_available_models(self) -> List[str]:
        """列出目前 API 金鑰可用的對話模型。此功能目前僅支援 Gemini。"""
        if self.model_provider != "gemini":
            print(f"'{self.model_provider}' 不支援動態列出模型。將使用設定檔中的預設模型。")
            return [self.model_name]

        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("錯誤：無法查詢可用模型，因為找不到 GEMINI_API_KEY。")
                return [self.model_name]
            # **修正**: 在查詢前，先用乾淨的狀態設定 API 金鑰
            genai.configure(api_key=api_key)

            print("正在向 Google 查詢可用的 Gemini 模型...")
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name.replace("models/", ""))
            print(f"找到 {len(available_models)} 個可用的對話模型。")
            return available_models if available_models else [self.model_name]
        except Exception as e:
            print(f"錯誤：查詢可用模型時失敗: {e}")
            return [self.model_name]

    def _build_ollama_messages(self, system_prompt: str, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """將我們的歷史紀錄格式轉換為 Ollama 需要的格式。"""
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history:
            role = "assistant" if turn["role"] != "user" else "user"
            messages.append({"role": role, "content": turn["content"]})
        return messages

    def generate_response(self, history: List[Dict[str, str]], available_modules: List[str], model_override_name: str = None) -> Tuple[str, str]:
        """生成回應。此版本會根據供應商動態呼叫 Gemini 或 Ollama。"""
        model_to_use = model_override_name if model_override_name else self.model_name
        system_prompt = self.construct_prompt(history, available_modules)
        print(f"--- 正在為 {self.module_id} (模型: {self.model_provider}/{model_to_use}) 呼叫 API ---")

        try:
            if self.model_provider == "gemini":
                model = genai.GenerativeModel(model_to_use, safety_settings=SAFETY_SETTINGS)
                response = model.generate_content(system_prompt)

                if not response.candidates:
                    feedback = response.prompt_feedback
                    block_reason = getattr(feedback, 'block_reason', '未知')
                    return f"抱歉，Gemini請求似乎因 '{block_reason}' 而被攔截。", "END"

                candidate = response.candidates[0]
                if candidate.finish_reason.name != "STOP":
                    return f"抱歉，AI因為 '{candidate.finish_reason.name}' 的原因提前中止了回應。", "END"

                # **修正**: 使用更安全的方式提取文字內容
                if candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
                else:
                    response_text = "" # 如果沒有內容部分，則回傳空字串

            elif self.model_provider == "ollama":
                if not self.client:
                     return f"錯誤：模組 '{self.module_id}' 的 Ollama 客戶端未被初始化。", "END"
                messages = self._build_ollama_messages(system_prompt, history)
                response = self.client.chat(model=model_to_use, messages=messages)
                response_text = response['message']['content']

            if self.output_parser == "json":
                cleaned_response_text = response_text.strip().replace("```json", "").replace("```", "").strip()
                parsed_output = json.loads(cleaned_response_text)
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