import gradio as gr
import time
from datetime import datetime
import json
import os
import requests

# 導入核心邏輯和檔案處理功能
from core_logic import run_main_chain, test_gemini_api_key, DEFAULT_ANALYST_TEMPLATE, DEFAULT_STRATEGIST_TEMPLATE, DEFAULT_CRITIC_TEMPLATE
from file_handler import save_to_json, load_from_json

# --- 應用程式狀態管理 ---
class AppState:
    def __init__(self):
        self.conversation_history = []
        self.meeting_topic = "創意激發會議"
        self.roles = [
            {"name": "文件分析師", "provider": "Ollama", "model_name": "llama3", "api_key": "", "prompt": DEFAULT_ANALYST_TEMPLATE},
            {"name": "創意策略師", "provider": "Ollama", "model_name": "llama3", "api_key": "", "prompt": DEFAULT_STRATEGIST_TEMPLATE},
            {"name": "批判性思考者", "provider": "Ollama", "model_name": "llama3", "api_key": "", "prompt": DEFAULT_CRITIC_TEMPLATE}
        ]

    def add_to_history(self, user_question: str, ai_response: dict):
        self.conversation_history.append({"user": user_question, "ai": ai_response})

    def format_history_for_display(self) -> str:
        display_text = ""
        for turn in self.conversation_history:
            display_text += f"👤 **使用者**: {turn['user']}\n\n"
            display_text += "🤖 **AI 團隊回覆**:\n"
            ai_outputs = turn['ai']
            if ai_outputs.get("error"):
                display_text += f"   - 🔴 **錯誤**: {ai_outputs['error']}\n\n"
            else:
                chain_keys = ["analysis", "strategies", "critique"]
                for i, role in enumerate(self.roles):
                    role_name = role.get("name", f"角色 {i+1}")
                    if i < len(chain_keys):
                        content = ai_outputs.get(chain_keys[i], "N/A")
                        display_text += f"   - **{role_name}**: {content}\n"
            display_text += "\n---\n"
        return display_text

    def reset(self):
        self.conversation_history = []
        self.meeting_topic = "創意激發會議"

state = AppState()

# --- UI 事件處理函式 ---
def update_meeting_topic(topic: str):
    state.meeting_topic = topic
    return f"主題已更新為: {topic}"

def get_ollama_models():
    """呼叫本地 Ollama API 來取得可用的模型列表。"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        # 使用 gr.update 來更新下拉選單的選項
        return gr.update(choices=model_names), "Ollama 模型列表已刷新。"
    except requests.exceptions.ConnectionError:
        return gr.update(), "無法連接至 Ollama 服務。請確認其正在本機運行。"
    except Exception as e:
        return gr.update(), f"刷新模型時發生錯誤: {e}"

def process_question(question: str, notes: str):
    if not question.strip():
        return state.format_history_for_display(), notes, "問題不能為空。"
    ai_response = run_main_chain(question, state.roles)
    state.add_to_history(question, ai_response)
    return state.format_history_for_display(), notes, f"'{question[:20]}...' 已處理完成。"

def export_session(notes: str):
    if not state.conversation_history and not notes.strip():
        return gr.update(visible=False), "沒有任何內容可匯出。"
    content = {"meeting_topic": state.meeting_topic, "export_time": datetime.now().isoformat(), "history": state.conversation_history, "notes": notes}
    filepath = save_to_json(state.meeting_topic, content, "session")
    return (gr.update(value=filepath, visible=True), f"會議已匯出至: {filepath}") if filepath else (gr.update(visible=False), "會議匯出失敗。")

def end_meeting(notes: str):
    _, export_status = export_session(notes)
    state.reset()
    return "", "", "創意激發會議", f"會議結束。\n{export_status}\n\n應用程式已重置。"

def restore_session(file_obj):
    if file_obj is None: return state.meeting_topic, state.format_history_for_display(), "", "未上傳任何檔案。"
    data = load_from_json(file_obj.name)
    if not data: return state.meeting_topic, state.format_history_for_display(), "", f"無法讀取或解析檔案: {file_obj.name}"
    state.meeting_topic = data.get("meeting_topic", "無標題")
    state.conversation_history = data.get("history", [])
    notes = data.get("notes", "")
    return state.meeting_topic, state.format_history_for_display(), notes, "會議紀錄已成功還原。"

def update_preview(text): return text
def toggle_settings(is_open): return gr.update(open=not is_open)

def save_roles(*args):
    num_roles = len(state.roles)
    for i in range(num_roles):
        state.roles[i]["name"], state.roles[i]["provider"], state.roles[i]["model_name"], state.roles[i]["api_key"], state.roles[i]["prompt"] = args[i*5:(i+1)*5]
    return "團隊設定已成功儲存於本次會話。"

def export_roles():
    filepath = save_to_json("InsightCascade_Team_Config", state.roles, "team_config")
    return (gr.update(value=filepath, visible=True), "團隊設定已匯出。") if filepath else (gr.update(visible=False), "團隊設定匯出失敗。")

def import_roles(file_obj):
    if file_obj is None: return "未上傳任何檔案。", *[gr.update() for _ in range(len(state.roles) * 7)]
    imported_roles = load_from_json(file_obj.name)
    if not isinstance(imported_roles, list): return "檔案格式不正確。", *[gr.update() for _ in range(len(state.roles) * 7)]
    state.roles = imported_roles
    updates = []
    for role in state.roles:
        is_ollama = role.get("provider") == "Ollama"
        updates.extend([gr.update(value=role.get("name", "")), gr.update(value=role.get("provider", "Ollama")), gr.update(value=role.get("model_name", "llama3")), gr.update(value=role.get("api_key", "")), gr.update(value=role.get("prompt", "")), gr.update(visible=is_ollama), gr.update(visible=not is_ollama)])
    return "團隊設定已成功匯入。", *updates

# --- Gradio UI 佈局 ---
with gr.Blocks(title="Insight Cascade", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🚀 Insight Cascade")
    meeting_topic_textbox = gr.Textbox(value=state.meeting_topic, label="會議主題", interactive=True)
    topic_status = gr.Markdown()
    with gr.Row():
        with gr.Column(scale=2): conversation_panel = gr.Textbox(label="AI 對話記錄", lines=25, interactive=False)
        with gr.Column(scale=3):
            gr.Markdown("### 主席筆記")
            with gr.Row():
                chairman_notes_editor = gr.Textbox(show_label=False, lines=23, interactive=True, placeholder="在此用 Markdown 語法輸入筆記...")
                chairman_notes_preview = gr.Markdown(label="即時預覽")
    with gr.Row():
        export_session_button = gr.Button("匯出會議紀錄")
        session_file_output = gr.File(label="下載會議紀錄檔案", visible=False)
    with gr.Column():
        question_input = gr.Textbox(label="您的問題", placeholder="請輸入您想探討的問題...")
        send_button = gr.Button("發送問題")
        end_meeting_button = gr.Button("結束會議並匯出全部")
    status_update = gr.Markdown()

    with gr.Accordion("團隊與AI設定 (Team & AI Settings)", open=False) as settings_accordion:
        with gr.Tabs() as role_tabs:
            role_ui_components = []
            all_role_inputs, all_role_outputs = [], []
            for i, role in enumerate(state.roles):
                with gr.Tab(label=f"角色 {i+1}", id=i):
                    name_input = gr.Textbox(label="角色名稱", value=role["name"])
                    provider_input = gr.Radio(["Ollama", "Gemini"], label="AI 提供商", value=role["provider"])
                    with gr.Group(visible=(role["provider"] == "Ollama")) as ollama_settings:
                        with gr.Row():
                            model_name_input = gr.Dropdown(["llama3", "mistral", "gemma"], label="Ollama 模型", value=role["model_name"], interactive=True)
                            refresh_ollama_button = gr.Button("🔄 刷新")
                    with gr.Group(visible=(role["provider"] == "Gemini")) as gemini_settings:
                        with gr.Row():
                            api_key_input = gr.Textbox(label="Gemini API 金鑰", value=role["api_key"], type="password", interactive=True, scale=3)
                            test_gemini_button = gr.Button("✔️ 測試金鑰", scale=1)
                    prompt_input = gr.Textbox(label="角色提示詞", value=role["prompt"], lines=8, interactive=True)

                    role_ui_components.append({
                        "provider": provider_input,
                        "ollama_group": ollama_settings,
                        "gemini_group": gemini_settings,
                        "ollama_model_dropdown": model_name_input,
                        "refresh_button": refresh_ollama_button,
                        "api_key_input": api_key_input,
                        "test_gemini_button": test_gemini_button
                    })
                    all_role_inputs.extend([name_input, provider_input, model_name_input, api_key_input, prompt_input])
                    all_role_outputs.extend([name_input, provider_input, model_name_input, api_key_input, prompt_input, ollama_settings, gemini_settings])

        with gr.Row():
            save_roles_button = gr.Button("儲存所有角色設定")
            export_roles_button = gr.Button("匯出團隊設定")
            import_roles_button = gr.UploadButton("匯入團隊設定 (.json)", file_types=["json"])
        roles_file_output = gr.File(label="下載團隊設定檔案", visible=False)

    with gr.Row(elem_classes=["footer"]):
        upload_button = gr.UploadButton("匯入會議紀錄 (.json)", file_types=["json"])
        gr.HTML("<div style='flex-grow: 1'></div>")
        settings_button = gr.Button("⚙️ 團隊設定")

    # --- 事件綁定 ---
    meeting_topic_textbox.submit(update_meeting_topic, inputs=meeting_topic_textbox, outputs=topic_status)
    send_button.click(process_question, inputs=[question_input, chairman_notes_editor], outputs=[conversation_panel, chairman_notes_editor, status_update])
    export_session_button.click(export_session, inputs=[chairman_notes_editor], outputs=[session_file_output, status_update])
    end_meeting_button.click(end_meeting, inputs=[chairman_notes_editor], outputs=[conversation_panel, chairman_notes_editor, meeting_topic_textbox, status_update]).then(lambda: "", outputs=question_input).then(lambda: "", outputs=chairman_notes_preview)
    upload_button.upload(restore_session, inputs=[upload_button], outputs=[meeting_topic_textbox, conversation_panel, chairman_notes_editor, status_update])
    chairman_notes_editor.change(update_preview, inputs=chairman_notes_editor, outputs=[chairman_notes_preview])
    settings_button.click(toggle_settings, inputs=[settings_accordion], outputs=[settings_accordion])

    def toggle_provider_settings(provider):
        is_ollama = provider == "Ollama"
        return gr.update(visible=is_ollama), gr.update(visible=not is_ollama)

    for components in role_ui_components:
        components["provider"].change(toggle_provider_settings, inputs=components["provider"], outputs=[components["ollama_group"], components["gemini_group"]])
        components["refresh_button"].click(get_ollama_models, outputs=[components["ollama_model_dropdown"], status_update])
        components["test_gemini_button"].click(test_gemini_api_key, inputs=[components["api_key_input"]], outputs=[status_update])

    save_roles_button.click(save_roles, inputs=all_role_inputs, outputs=[status_update])
    export_roles_button.click(export_roles, outputs=[roles_file_output, status_update])
    import_roles_button.upload(import_roles, inputs=[import_roles_button], outputs=[status_update, *all_role_outputs])

# --- 啟動應用程式 ---
if __name__ == "__main__":
    app.launch(debug=True)
