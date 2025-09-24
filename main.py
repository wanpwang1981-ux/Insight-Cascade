import sys
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數 (例如 API 金鑰)
# 這應該在所有其他匯入和程式碼之前執行
load_dotenv()

# 將 'src' 目錄加入到 Python 的搜尋路徑中，以便可以直接匯入 src 下的模組
sys.path.append('src')

from orchestrator import Orchestrator

# 定義儲存模組設定檔的目錄路徑
MODULES_CONFIG_DIR = "configs/modules"

def main():
    """
    AI-Collab-Chat 應用程式的主要進入點。
    """
    print("正在初始化 AI 協作聊天系統...")

    # 步驟 1: 初始化協調者 (Orchestrator)
    # 這個過程會自動掃描、載入所有模組，並設定每個模組的 AI 連線。
    orchestrator = Orchestrator(modules_config_dir=MODULES_CONFIG_DIR)

    # 步驟 2: 檢查是否有任何模組被成功載入
    if not orchestrator.modules:
        print("嚴重錯誤: 找不到任何聊天模組。請檢查設定目錄。")
        print(f"搜尋路徑: {MODULES_CONFIG_DIR}")
        return # 結束應用程式

    # 步驟 3: 提示使用者輸入一個初始主題
    try:
        initial_prompt = input("請輸入一個主題來開始對話: ")
    except KeyboardInterrupt:
        print("\n正在結束應用程式。")
        return

    # 步驟 4: 指定開始對話的模組
    # 在未來的版本中，這裡可以設計成動態選擇。
    start_module_id = "creative_bot_v1"

    # 安全檢查，確保指定的起始模組存在
    if start_module_id not in orchestrator.modules:
        print(f"嚴重錯誤: 找不到指定的起始模組 '{start_module_id}'。")
        return

    # 步驟 5: 執行對話
    orchestrator.run_conversation(
        initial_prompt=initial_prompt,
        start_module_id=start_module_id
    )

# Python 的標準寫法：確保當這個檔案被直接執行時，main() 函式會被呼叫
if __name__ == "__main__":
    main()
