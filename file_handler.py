import json
import os
from datetime import datetime

OUTPUTS_DIR = "outputs"

def save_to_json(meeting_topic: str, content: dict, file_type: str):
    """
    將內容以結構化的 JSON 格式儲存。

    Args:
        meeting_topic (str): 會議主題，用於檔案命名。
        content (dict): 要儲存的內容 (例如對話紀錄或筆記)。
        file_type (str): 檔案類型 ('conversation' 或 'notes')。

    Returns:
        str: 儲存的檔案路徑。
    """
    # 確保 outputs 資料夾存在
    if not os.path.exists(OUTPUTS_DIR):
        os.makedirs(OUTPUTS_DIR)

    # 格式化檔案名稱
    timestamp = datetime.now().strftime("%Y%m%d")
    # 替換掉主題中不適合當作檔名的字元，僅保留 ASCII 英數字、底線、橫線
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    safe_topic = "".join(c if c in allowed_chars else '_' for c in meeting_topic)
    filename = f"{safe_topic}_{timestamp}_{file_type}.json"
    filepath = os.path.join(OUTPUTS_DIR, filename)

    # 寫入 JSON 檔案
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        print(f"成功儲存檔案至: {filepath}")
        return filepath
    except Exception as e:
        print(f"儲存檔案時發生錯誤: {e}")
        return None

def load_from_json(filepath: str) -> dict:
    """
    從指定的路徑讀取 JSON 檔案並解析。

    Args:
        filepath (str): JSON 檔案的路徑。

    Returns:
        dict: 解析後的字典內容，如果失敗則返回 None。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"成功從 {filepath} 讀取資料。")
        return data
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"錯誤: {filepath} 的 JSON 格式不正確。")
        return None
    except Exception as e:
        print(f"讀取檔案時發生預期外的錯誤: {e}")
        return None

if __name__ == '__main__':
    # 用於單元測試的範例
    print("執行 file_handler.py 單元測試...")

    # --- 測試寫入 ---
    mock_topic = "測試會議主題"
    mock_conversation = {
        "meeting_topic": mock_topic,
        "timestamp": datetime.now().isoformat(),
        "history": [
            {"role": "user", "content": "我們的第一季目標是什麼？"},
            {"role": "AI-Analyst", "content": "根據數據，第一季目標是提升使用者活躍度15%。"}
        ]
    }
    mock_notes = {
        "meeting_topic": mock_topic,
        "timestamp": datetime.now().isoformat(),
        "notes": "主席認為需要關注使用者留存率，而不僅僅是活躍度。"
    }

    # 測試儲存對話
    conv_path = save_to_json(mock_topic, mock_conversation, "conversation")
    if conv_path and os.path.exists(conv_path):
        print(f"對話紀錄檔案已成功創建於: {conv_path}")
        # os.remove(conv_path) # 清理測試檔案
    else:
        print("對話紀錄檔案創建失敗。")

    # 測試儲存筆記
    notes_path = save_to_json(mock_topic, mock_notes, "notes")
    if notes_path and os.path.exists(notes_path):
        print(f"主席筆記檔案已成功創建於: {notes_path}")
        # os.remove(notes_path) # 清理測試檔案
    else:
        print("主席筆記檔案創建失敗。")

    # --- 測試讀取 ---
    print("\n--- 測試讀取功能 ---")
    if conv_path:
        loaded_data = load_from_json(conv_path)
        if loaded_data and loaded_data["meeting_topic"] == mock_topic:
            print("讀取並驗證對話紀錄成功。")
        else:
            print("讀取或驗證對話紀錄失敗。")

    # 測試清理
    if conv_path and os.path.exists(conv_path):
        os.remove(conv_path)
    if notes_path and os.path.exists(notes_path):
        os.remove(notes_path)
    print("\n單元測試結束。")
