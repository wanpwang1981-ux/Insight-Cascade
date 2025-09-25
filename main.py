import sys
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數 (例如 API 金鑰)
load_dotenv()

# 將 'src' 目錄加入到 Python 的搜尋路徑中
sys.path.append('src')

from orchestrator import Orchestrator

# 定義儲存模組設定檔的目錄路徑
MODULES_CONFIG_DIR = "configs/modules"

def select_start_module(modules: list) -> str:
    """
    顯示可用模組列表，並提示使用者選擇一個作為起始模組。
    """
    print("\n請選擇一個起始模組來開始對話：")
    for i, module_id in enumerate(modules):
        print(f"  {i + 1}: {module_id}")

    while True:
        try:
            choice = input(f"請輸入選項 (1-{len(modules)}): ")
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(modules):
                return modules[choice_index]
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

    # 步驟 1: 初始化協調者 (Orchestrator)
    orchestrator = Orchestrator(modules_config_dir=MODULES_CONFIG_DIR)

    # 步驟 2: 檢查是否有任何模組被成功載入
    if not orchestrator.modules:
        print("嚴重錯誤: 找不到任何聊天模組。請檢查設定目錄。")
        return

    # 步驟 3: 讓使用者選擇起始模組
    module_ids = list(orchestrator.modules.keys())
    start_module_id = select_start_module(module_ids)

    if not start_module_id:
        print("未選擇任何模組，程式結束。")
        return

    print(f"\n您已選擇 '{start_module_id}' 作為起始模組。")

    # 步驟 4: 提示使用者輸入一個初始主題
    try:
        initial_prompt = input("請輸入一個主題來開始對話: ")
    except (KeyboardInterrupt, EOFError):
        print("\n正在結束應用程式。")
        return

    # 步驟 5: 執行對話
    orchestrator.run_conversation(
        initial_prompt=initial_prompt,
        start_module_id=start_module_id
    )

# Python 的標準寫法：確保當這個檔案被直接執行時，main() 函式會被呼叫
if __name__ == "__main__":
    main()