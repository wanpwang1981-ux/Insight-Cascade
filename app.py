import gradio as gr
import time
from datetime import datetime

# 導入核心邏輯和檔案處理功能
from core_logic import run_main_chain
from file_handler import save_to_json

# --- 應用程式狀態管理 ---
# 使用一個簡單的 class 來管理狀態，避免使用全域變數
class AppState:
    def __init__(self):
        self.conversation_history = []
        self.meeting_topic = "創意激發會議"

    def add_to_history(self, user_question: str, ai_response: dict):
        self.conversation_history.append({"user": user_question, "ai": ai_response})

    def format_history_for_display(self) -> str:
        display_text = ""
        for turn in self.conversation_history:
            display_text += f"👤 使用者: {turn['user']}\n\n"
            display_text += "🤖 AI 團隊回覆:\n"
            display_text += f"   [分析師]: {turn['ai'].get('analysis', 'N/A')}\n"
            display_text += f"   [策略師]: {turn['ai'].get('strategies', 'N/A')}\n"
            display_text += f"   [批判者]: {turn['ai'].get('critique', 'N/A')}\n\n"
            display_text += "---\n"
        return display_text

    def reset(self):
        self.conversation_history = []
        self.meeting_topic = "創意激發會議"

state = AppState()

# --- UI 事件處理函式 ---

def update_meeting_topic(topic: str):
    """更新會議主題"""
    state.meeting_topic = topic
    return f"主題已更新為: {topic}"

def process_question(question: str, notes: str):
    """處理使用者問題，並更新對話紀錄和筆記"""
    if not question.strip():
        return state.format_history_for_display(), notes, "問題不能為空。"

    # 執行 AI 鏈
    ai_response = run_main_chain(question)

    # 更新歷史紀錄
    state.add_to_history(question, ai_response)

    # 返回更新後的 UI 內容
    return state.format_history_for_display(), notes, f"'{question[:20]}...' 已處理完成。"

def export_conversation():
    """匯出對話紀錄"""
    if not state.conversation_history:
        return "對話紀錄為空，無法匯出。"

    content = {
        "meeting_topic": state.meeting_topic,
        "export_time": datetime.now().isoformat(),
        "history": state.conversation_history
    }
    filepath = save_to_json(state.meeting_topic, content, "conversation")
    return f"對話紀錄已匯出至: {filepath}" if filepath else "匯出失敗。"

def export_notes(notes: str):
    """匯出主席筆記"""
    if not notes.strip():
        return "筆記為空，無法匯出。"

    content = {
        "meeting_topic": state.meeting_topic,
        "export_time": datetime.now().isoformat(),
        "notes": notes
    }
    filepath = save_to_json(state.meeting_topic, content, "notes")
    return f"主席筆記已匯出至: {filepath}" if filepath else "匯出失敗。"

def end_meeting(notes: str):
    """結束會議並匯出所有內容"""
    conv_msg = export_conversation()
    notes_msg = export_notes(notes)

    # 重置狀態
    state.reset()

    return "", "", f"會議結束。\n{conv_msg}\n{notes_msg}\n\n應用程式已重置，可以開始新會議。"

# --- Gradio UI 佈局 ---
with gr.Blocks(title="Insight Cascade", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🚀 Insight Cascade")

    meeting_topic_textbox = gr.Textbox(
        value=state.meeting_topic,
        label="會議主題 (Meeting Topic)",
        interactive=True
    )
    topic_status = gr.Markdown()
    meeting_topic_textbox.submit(update_meeting_topic, inputs=meeting_topic_textbox, outputs=topic_status)

    # 中部工作區
    with gr.Row():
        with gr.Column():
            conversation_panel = gr.Textbox(
                label="AI 對話記錄 (Conversation Panel)",
                lines=20,
                interactive=False
            )
            export_conv_button = gr.Button("匯出對話紀錄")

        with gr.Column():
            chairman_notes = gr.Textbox(
                label="主席筆記 (Chairman's Notes)",
                lines=20,
                interactive=True,
                placeholder="在此輸入您的想法、決策和行動項目..."
            )
            export_notes_button = gr.Button("匯出主席筆記")

    # 底部控制欄
    with gr.Column():
        question_input = gr.Textbox(label="您的問題 (Your Question)", placeholder="請輸入您想探討的問題...")
        send_button = gr.Button("發送問題")
        end_meeting_button = gr.Button("結束會議並匯出全部")

    status_update = gr.Markdown()

    # 頁腳
    with gr.Row(elem_classes=["footer"]):
        gr.HTML("<div style='flex-grow: 1'></div>") # Spacer
        gr.Markdown("設定 v0.1.0-MVP", elem_classes=["version-label"])

    # --- 連接事件與函式 ---
    send_button.click(
        process_question,
        inputs=[question_input, chairman_notes],
        outputs=[conversation_panel, chairman_notes, status_update]
    )

    export_conv_button.click(export_conversation, outputs=status_update)
    export_notes_button.click(export_notes, inputs=chairman_notes, outputs=status_update)

    end_meeting_button.click(
        end_meeting,
        inputs=[chairman_notes],
        outputs=[conversation_panel, chairman_notes, status_update]
    ).then(lambda: "", outputs=question_input) # 清空問題輸入框

# --- 啟動應用程式 ---
if __name__ == "__main__":
    app.launch()
