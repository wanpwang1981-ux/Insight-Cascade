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
        self.modules: Dict[str, ChatModule] = self._load_modules(modules_config_dir)
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
                module = ChatModule(config_path=config_path)
                if module.module_id != "unknown_module":
                    print(f"  - 已載入模組: {module.module_id}")
                    loaded_modules[module.module_id] = module

        if not loaded_modules:
            print("警告: 未載入任何模組。")

        return loaded_modules

    def run_conversation(self, initial_prompt: str, start_module_id: str, model_override_name: str = None):
        """
        執行主對話循環。
        可以接受一個臨時的模型名稱來覆寫本次對話的預設模型。
        """
        print("\n--- 對話開始 ---")

        self.history.append({"role": "user", "content": initial_prompt})
        print(f"使用者: {initial_prompt}\n")

        current_module_id = start_module_id
        available_module_ids = list(self.modules.keys())

        # 第一次對話使用使用者指定的模型
        # 後續的對話（如果有的話）將使用它們各自設定檔中的預設模型
        is_first_turn = True

        while current_module_id != "END":
            if current_module_id not in self.modules:
                print(f"錯誤: 找不到模組 '{current_module_id}'。對話結束。")
                break

            current_module = self.modules[current_module_id]

            model_for_this_turn = model_override_name if is_first_turn else None

            response_text, next_module_id = current_module.generate_response(
                history=self.history,
                available_modules=available_module_ids,
                model_override_name=model_for_this_turn
            )

            is_first_turn = False # 只有第一輪使用覆寫的模型

            print(f"{current_module.module_id}: {response_text}\n")

            self.history.append({"role": current_module.module_id, "content": response_text})

            current_module_id = next_module_id

        print("--- 對話結束 ---")
