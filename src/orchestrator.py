import os
import json
from typing import List, Dict, Any

# 匯入我們剛剛建立的 ChatModule 類別
from chat_module import ChatModule

class Orchestrator:
    """
    AI 聊天系統的主要協調者。
    它負責載入所有聊天模組、管理對話流程並維護完整的對話歷史。
    """
    def __init__(self, modules_config_dir: str):
        """
        初始化協調者 (Orchestrator)。

        Args:
            modules_config_dir (str): 儲存模組 JSON 設定檔的目錄路徑。
        """
        # 屬性：一個字典，用來存放所有已載入的聊天模組實例，以 module_id 為鍵
        self.modules: Dict[str, ChatModule] = self._load_modules(modules_config_dir)
        # 屬性：一個列表，用來記錄完整的對話歷史
        self.history: List[Dict[str, str]] = []

    def _load_modules(self, config_dir: str) -> Dict[str, ChatModule]:
        """
        私有方法：掃描指定目錄中的 .json 檔案，並將每一個檔案載入為一個 ChatModule。
        """
        loaded_modules = {}
        if not os.path.isdir(config_dir):
            print(f"錯誤: 在 {config_dir} 找不到模組設定目錄")
            return {}

        print(f"正在掃描目錄中的模組: {config_dir}")
        for filename in os.listdir(config_dir):
            if filename.endswith(".json"):
                config_path = os.path.join(config_dir, filename)
                # 為每個設定檔建立一個 ChatModule 實例
                module = ChatModule(config_path=config_path)
                if module.module_id != "unknown_module":
                    print(f"  - 已載入模組: {module.module_id}")
                    # 將模組實例存入字典
                    loaded_modules[module.module_id] = module

        if not loaded_modules:
            print("警告: 未載入任何模組。")

        return loaded_modules

    def run_conversation(self, initial_prompt: str, start_module_id: str):
        """
        執行主對話循環。

        Args:
            initial_prompt (str): 來自使用者的第一則訊息。
            start_module_id (str): 開始對話的模組 ID。
        """
        print("\n--- 對話開始 ---")

        # 將使用者的初始訊息加入歷史紀錄
        self.history.append({"role": "user", "content": initial_prompt})
        print(f"使用者: {initial_prompt}\n")

        current_module_id = start_module_id

        # 循環將持續進行，直到下一個模組的 ID 為 "END"
        while current_module_id != "END":
            # 安全檢查：確保要呼叫的模組存在
            if current_module_id not in self.modules:
                print(f"錯誤: 找不到模組 '{current_module_id}'。對話結束。")
                break

            # 從字典中取得目前的模組實例
            current_module = self.modules[current_module_id]

            # 模組生成回應，並建議下一個模組
            response_text, next_module_id = current_module.generate_response(self.history)

            # 在主控台印出回應，方便追蹤
            print(f"{current_module.module_id}: {response_text}\n")

            # 將模組的回應加入歷史紀錄
            self.history.append({"role": current_module.module_id, "content": response_text})

            # 更新為下一個模組的 ID，以進行下一輪循環
            current_module_id = next_module_id

        print("--- 對話結束 ---")
