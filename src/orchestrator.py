import os
import json
from typing import List, Dict, Any
from datetime import datetime

from chat_module import ChatModule

class Orchestrator:
    """
    AI 聊天系統的主要協調者。
    它負責載入所有聊天模組、管理對話流程並維護完整的對話歷史。
    """
    def __init__(self, modules_config_dir: str):
        """
        初始化協調者 (Orchestrator)。
        """
        self.modules: Dict[str, ChatModule] = self._load_modules(modules_config_dir)
        self.history: List[Dict[str, Any]] = []

    def load_history(self, history_data: List[Dict[str, Any]]):
        """從外部載入一個已存在的對話歷史。"""
        self.history = history_data
        print(f"已成功載入 {len(self.history)} 則對話紀錄。")

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

    def add_to_history(self, role: str, content: Any):
        """一個公開的輔助函式，用來將帶有時間戳的紀錄加入歷史。"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(entry)
        # 只有使用者的新提示需要明確印出，AI的回應由主循環處理
        if role == "user":
            print(f"使用者: {content}\n")

    def run_conversation_loop(self, start_module_id: str, model_override_name: str = None):
        """
        執行主對話循環。這個函式現在假設對話歷史中已經至少有一則訊息。
        """
        print("\n--- 對話開始 ---")

        current_module_id = start_module_id
        available_module_ids = list(self.modules.keys())
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

            is_first_turn = False

            print(f"{current_module.module_id}: {response_text}\n")

            # **修正**: 呼叫正確的公開方法 add_to_history
            self.add_to_history(current_module.module_id, response_text)

            current_module_id = next_module_id

        print("--- 對話結束 ---")
        self.save_memory()

    def save_memory(self):
        """將目前的對話歷史儲存到 memory/ 資料夾中。"""
        if not self.history:
            print("對話歷史為空，無需儲存。")
            return

        if not os.path.exists("memory"):
            os.makedirs("memory")
            print("已建立 memory/ 資料夾。")

        timestamp_str = self.history[0]["timestamp"].replace(":", "-").replace(".", "-")
        filename = f"memory/conversation_{timestamp_str}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
            print(f"對話歷史已成功儲存至: {filename}")
        except Exception as e:
            print(f"錯誤：儲存對話歷史時失敗: {e}")