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
MODELS_CONFIG_PATH = "configs/models.json"
MEMORY_DIR = "memory"

def select_from_list(options: list, prompt_message: str, allow_cancel: bool = False) -> str:
    """一個通用的函式，用來顯示一個列表並讓使用者從中選擇一項。"""
    print(f"\n{prompt_message}")
    for i, option in enumerate(options):
        # 檢查選項是否為字典 (用於我的最愛模型)
        if isinstance(option, dict):
            display_name = option['name']
            if option.get('is_favorite'):
                display_name += " (★ 我的最愛)"
            print(f"  {i + 1}: {display_name}")
        else:
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
                # 如果選項是字典，回傳其 'name'
                selected_option = options[choice_index - 1]
                return selected_option['name'] if isinstance(selected_option, dict) else selected_option
            else:
                print("錯誤：無效的選項，請重新輸入。")
        except ValueError:
            print("錯誤：請輸入一個數字。")
        except (KeyboardInterrupt, EOFError):
            print("\n操作已取消。")
            return None

def load_models_from_config(provider: str) -> list:
    """從 models.json 讀取指定供應商的模型列表。"""
    try:
        with open(MODELS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            all_models = json.load(f)

        provider_models = all_models.get(provider, [])
        # 排序：我的最愛優先，然後按名稱排序
        provider_models.sort(key=lambda x: (not x.get('is_favorite', False), x['name']))
        return provider_models
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"警告：找不到或無法解析 {MODELS_CONFIG_PATH}。將無法從設定檔載入模型列表。")
        return []

def main():
    """AI-Collab-Chat 應用程式的主要進入點。"""
    print("正在初始化 AI 協作聊天系統...")
    orchestrator = Orchestrator(modules_config_dir=MODULES_CONFIG_DIR)

    if not orchestrator.modules:
        print("嚴重錯誤: 找不到任何聊天模組。請檢查設定目錄。")
        return

    # **頂層選單：新對話或載入記憶**
    # (此部分邏輯不變，省略以求簡潔)
    main_choice = select_from_list(["開始新對話", "載入舊記憶"], "請問您想做什麼？")
    if not main_choice: print("程式結束。"); return
    if main_choice == "載入舊記憶":
        # ... (載入記憶的邏輯) ...
        pass # 簡化表示

    # **通用流程：選擇角色 -> 選擇模型 -> 輸入提示**
    module_ids = list(orchestrator.modules.keys())
    start_module_id = select_from_list(module_ids, "請選擇一個 AI 角色來繼續對話：")
    if not start_module_id: print("未選擇任何角色，程式結束。"); return

    selected_module = orchestrator.modules[start_module_id]
    print(f"\n您已選擇 '{start_module_id}'。")

    # **全新的模型選擇流程**
    model_to_use = None
    if selected_module.model_provider == "ollama":
        # 對於 Ollama，動態查詢本地模型
        available_models = selected_module.list_available_models()
        if not available_models:
            print("錯誤：找不到任何可用的 Ollama 模型。")
            return
        model_to_use = select_from_list(available_models, f"請為 '{start_module_id}' (Ollama) 選擇要使用的模型：")
    else:
        # 對於 Gemini (或其他未來 API)，從設定檔載入
        available_models = load_models_from_config(selected_module.model_provider)
        if not available_models:
            print(f"警告：在 {MODELS_CONFIG_PATH} 中找不到為 '{selected_module.model_provider}' 設定的模型。將使用模組的預設模型。")
            model_to_use = selected_module.model_name
        else:
            model_to_use = select_from_list(available_models, f"請為 '{start_module_id}' ({selected_module.model_provider}) 選擇要使用的模型：")

    if not model_to_use: print("未選擇任何模型，程式結束。"); return
    print(f"\n您已選擇使用模型：'{model_to_use}'。")

    # **輸入對話主題**
    try:
        prompt_text = "請輸入您的下一句話: " if orchestrator.history else "請輸入一個主題來開始對話: "
        new_prompt = input(prompt_text)
    except (KeyboardInterrupt, EOFError):
        print("\n正在結束應用程式。"); return

    orchestrator.add_to_history("user", new_prompt)

    # **執行對話循環**
    orchestrator.run_conversation_loop(
        start_module_id=start_module_id,
        model_override_name=model_to_use
    )

if __name__ == "__main__":
    main()