import json
from typing import List, Dict, Tuple, Any

class ChatModule:
    """
    代表一個獨立的 AI 聊天模組（一個 AI 角色）。
    它會從一個設定檔進行初始化，並根據其角色設定和對話歷史來生成回應。
    """
    def __init__(self, config_path: str):
        """
        透過載入其設定檔來初始化聊天模組。

        Args:
            config_path (str): 此模組的 JSON 設定檔路徑。
        """
        # 載入設定檔並賦值給各個屬性
        self.config = self._load_config(config_path)
        self.module_id: str = self.config.get("module_id", "unknown_module")
        self.character_setting: str = self.config.get("character_setting", "")
        self.model_endpoint: str = self.config.get("model_endpoint", "")
        # 未來，這些解析器和選擇器可以發展成更複雜的類別或函式
        self.output_parser = self.config.get("output_parser", "default")
        self.next_module_selector = self.config.get("next_module_selector", "end_conversation")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        私有方法：載入指定路徑的 JSON 設定檔。

        Returns:
            一個包含設定資訊的字典。
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 在正式應用中，此處應使用更穩健的錯誤處理或日誌記錄
            print(f"錯誤：在 {config_path}找不到設定檔")
            return {}
        except json.JSONDecodeError:
            print(f"錯誤：無法解析 {config_path} 的 JSON 內容")
            return {}

    def construct_prompt(self, history: List[Dict[str, str]]) -> str:
        """
        為 AI 模型建構一個詳細的提示 (Prompt)，包含角色設定和對話歷史。

        Args:
            history (List[Dict[str, str]]): 對話的先前回合列表。
                                           範例: [{"role": "user", "content": "你好！"}]

        Returns:
            一個代表完整提示的字串。
        """
        # 這是一個非常基礎的提示工程範例，未來可以使其更為複雜精緻。
        prompt = f"系統提示: {self.character_setting}\n\n"
        prompt += "對話歷史:\n"
        for turn in history:
            prompt += f"- {turn['role']}: {turn['content']}\n"

        prompt += "\n你的任務: 請根據你的角色設定和以上的對話歷史，提供你的回應。"
        return prompt

    def generate_response(self, history: List[Dict[str, str]]) -> Tuple[str, str]:
        """
        生成回應。在此版本中，這是一個模擬的回應，並不會真的呼叫 AI 模型。

        Args:
            history (List[Dict[str, str]]): 對話歷史。

        Returns:
            一個包含以下內容的元組 (tuple):
            - 生成的回應文字 (str)。
            - 下一個要啟動的模組 ID (str)。
        """
        # 建立提示，以展示它將如何被使用
        prompt = self.construct_prompt(history)
        print(f"--- 正在為 {self.module_id} 進行模擬 AI 呼叫 ---")
        print(f"--- 發送至模型的提示: ---\n{prompt}\n------------------------------")

        # 來自 AI 的模擬回應文字
        mock_response_text = "這是一個來自創意機器人的模擬回覆！想法一：... 想法二：... 想法三：..."

        # 根據設定檔中的簡單邏輯來決定下一個模組
        next_module = self.next_module_selector
        if next_module == "end_conversation":
            next_module = "END" # 使用一個標準化的關鍵字來結束對話

        return mock_response_text, next_module
