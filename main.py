import sys
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數 (例如 API 金鑰)
load_dotenv()

# 將 'src' 目錄加入到 Python 的搜尋路徑中
sys.path.append('src')

from orchestrator import Orchestrator

# 定義儲存模組設定檔的目錄路徑
MODULES_CONFIG_DIR = "configs/modules"

def select_from_list(options: list, prompt_message: str) -> str:
    """
    一個通用的函式，用來顯示一個列表並讓使用者從中選擇一項。
    """
    print(f"\n{prompt_message}")
    for i, option in enumerate(options):
        print(f"  {i + 1}: {option}")

    while True:
        try:
            choice = input(f"請輸入選項 (1-{len(options)}): ")
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(options):
                return options[choice_index]
            else:
                print("錯誤：無效的選項，請重新輸入。")
        except ValueError:
            print("錯誤：請輸入一個數字。")
        except (KeyboardInterrupt, EOFError):
            print("\n操作已取消。")
            return None

def main():
    """
    AI-Collab-Chat 應用程式的主要進入點。
    """
    print("正在初始化 AI 協作聊天系統...")

    orchestrator = Orchestrator(modules_config_dir=MODULES_CONFIG_DIR)

    if not orchestrator.modules:
        print("嚴重錯誤: 找不到任何聊天模組。請檢查設定目錄。")
        return

    # **流程第一步：選擇 AI 角色**
    module_ids = list(orchestrator.modules.keys())
    start_module_id = select_from_list(module_ids, "請選擇一個起始 AI 角色來開始對話：")

    if not start_module_id:
        print("未選擇任何角色，程式結束。")
        return

    selected_module = orchestrator.modules[start_module_id]
    print(f"\n您已選擇 '{start_module_id}'。")

    # **流程第二步：選擇要使用的模型**
    # 讓選擇的模組去查詢可用的模型列表
    available_models = selected_module.list_available_models()

    # 如果只有一個模型可用（例如 Ollama 或查詢失敗），則直接使用
    if len(available_models) == 1:
        model_to_use = available_models[0]
        print(f"將使用預設模型：'{model_to_use}'。")
    else:
        # 如果有多個模型，讓使用者選擇
        model_to_use = select_from_list(available_models, f"請為 '{start_module_id}' 選擇要使用的模型：")

    if not model_to_use:
        print("未選擇任何模型，程式結束。")
        return

    print(f"\n您已選擇使用模型：'{model_to_use}'。")

    # **流程第三步：輸入對話主題**
    try:
        initial_prompt = input("請輸入一個主題來開始對話: ")
    except (KeyboardInterrupt, EOFError):
        print("\n正在結束應用程式。")
        return

    # **流程第四步：執行對話**
    orchestrator.run_conversation(
        initial_prompt=initial_prompt,
        start_module_id=start_module_id,
        model_override_name=model_to_use # 將使用者選擇的模型傳遞下去
    )

if __name__ == "__main__":
    main()