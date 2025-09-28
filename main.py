import sys
import os
import json
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# 將 'src' 目錄加入到 Python 的搜尋路徑中
sys.path.append('src')

from orchestrator import Orchestrator

# 定義路徑
MODULES_CONFIG_DIR = "configs/modules"
MEMORY_DIR = "memory"

def select_from_list(options: list, prompt_message: str, allow_cancel: bool = False) -> str:
    """一個通用的函式，用來顯示一個列表並讓使用者從中選擇一項。"""
    print(f"\n{prompt_message}")
    for i, option in enumerate(options):
        print(f"  {i + 1}: {option}")
    if allow_cancel:
        print(f"  0: 取消")

    while True:
        try:
            choice_str = input(f"請輸入選項: ")
            choice_index = int(choice_str)

            if allow_cancel and choice_index == 0:
                return None

            if 1 <= choice_index <= len(options):
                return options[choice_index - 1]
            else:
                print("錯誤：無效的選項，請重新輸入。")
        except ValueError:
            print("錯誤：請輸入一個數字。")
        except (KeyboardInterrupt, EOFError):
            print("\n操作已取消。")
            return None

def main():
    """AI-Collab-Chat 應用程式的主要進入點。"""
    print("正在初始化 AI 協作聊天系統...")
    orchestrator = Orchestrator(modules_config_dir=MODULES_CONFIG_DIR)

    if not orchestrator.modules:
        print("嚴重錯誤: 找不到任何聊天模組。請檢查設定目錄。")
        return

    # **頂層選單：新對話或載入記憶**
    main_menu_options = ["開始新對話", "載入舊記憶"]
    main_choice = select_from_list(main_menu_options, "請問您想做什麼？")

    if not main_choice:
        print("程式結束。")
        return

    if main_choice == "載入舊記憶":
        if not os.path.exists(MEMORY_DIR) or not os.listdir(MEMORY_DIR):
            print("找不到任何記憶檔案。將開始新對話...")
        else:
            memory_files = sorted([f for f in os.listdir(MEMORY_DIR) if f.endswith(".json")], reverse=True)
            selected_file = select_from_list(memory_files, "請選擇要載入的對話歷史：", allow_cancel=True)
            if selected_file:
                try:
                    with open(os.path.join(MEMORY_DIR, selected_file), 'r', encoding='utf-8') as f:
                        history_data = json.load(f)
                    orchestrator.load_history(history_data)
                    print(f"--- 歷史紀錄 ---")
                    for turn in orchestrator.history:
                        print(f"{turn['role']}: {turn['content'][:80]}...") # 顯示摘要
                    print(f"--- 歷史紀錄結束 ---")
                except Exception as e:
                    print(f"錯誤：讀取記憶檔案時失敗: {e}。將開始新對話...")
            else:
                print("取消載入。將開始新對話...")

    # **通用流程：選擇角色 -> 選擇模型 -> 輸入提示**
    # 選擇 AI 角色
    module_ids = list(orchestrator.modules.keys())
    start_module_id = select_from_list(module_ids, "請選擇一個 AI 角色來繼續對話：")
    if not start_module_id:
        print("未選擇任何角色，程式結束。")
        return

    selected_module = orchestrator.modules[start_module_id]
    print(f"\n您已選擇 '{start_module_id}'。")

    # 選擇對話模型
    available_models = selected_module.list_available_models()
    if len(available_models) == 1:
        model_to_use = available_models[0]
        print(f"將使用預設模型：'{model_to_use}'。")
    else:
        model_to_use = select_from_list(available_models, f"請為 '{start_module_id}' 選擇要使用的模型：")

    if not model_to_use:
        print("未選擇任何模型，程式結束。")
        return
    print(f"\n您已選擇使用模型：'{model_to_use}'。")

    # 輸入對話主題
    try:
        # 如果是新對話，提示詞是「主題」；如果是接續對話，則是「下一句話」
        prompt_text = "請輸入您的下一句話: " if orchestrator.history else "請輸入一個主題來開始對話: "
        new_prompt = input(prompt_text)
    except (KeyboardInterrupt, EOFError):
        print("\n正在結束應用程式。")
        return

    # 將新的使用者提示加入歷史
    orchestrator.add_to_history("user", new_prompt)

    # 執行對話循環
    orchestrator.run_conversation_loop(
        start_module_id=start_module_id,
        model_override_name=model_to_use
    )

if __name__ == "__main__":
    main()