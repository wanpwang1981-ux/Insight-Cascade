# Insight Cascade v0.1.0-MVP

## 專案總覽 (Project Overview)
Insight Cascade 是一個旨在分三階段演進的 AI 專家對話平台。本階段 (Phase 1) 的目標是開發一個功能完整的單人會議輔助工具 MVP (Minimum Viable Product)，專注於核心的 AI 對話鏈與內容匯出功能。

---

## UI 佈局與功能 (UI Layout & Features)

應用程式介面將使用 Gradio 構建，佈局分為四個主要區塊：

1.  **頂部 - 狀態欄 (Status Bar)**
    - **左上角**: `gr.Label` 顯示版本號 (`v0.1.0-MVP`) 和即時系統時間。
    - **中間**: `gr.Textbox` 用於設定會議主題，預設值為「創意激發會議」。

2.  **中部 - 雙欄工作區 (Workspace)**
    - **左側：AI 對話記錄框 (Conversation Panel)**
        - `gr.Textbox` (不可編輯) 用於顯示所有 AI 的回覆。
        - `gr.Button` 提供「匯出對話紀錄」功能。
    - **右側：主席筆記區 (Chairman's Notes)**
        - `gr.Textbox` (可編輯) 作為主觀筆記的輸入區域。
        - `gr.Button` 提供「匯出主席筆記」功能。

3.  **底部 - 主席控制欄 (Control Bar)**
    - `gr.Textbox` 作為主要的提問輸入框。
    - `gr.Button` 用於「發送問題」。
    - `gr.Button` 用於「結束會議」，點擊後會觸發所有內容的匯出。

---

## 核心工作流程 (Core Workflow)

```mermaid
graph TD
    A[使用者開啟應用程式] --> B{設定會議主題};
    B --> C{輸入問題};
    C -- 點擊「發送問題」 --> D[核心邏輯: SequentialChain 啟動];
    D --> E[AI-1: 文件分析師];
    E --> F[AI-2: 創意策略師];
    F --> G[AI-3: 批判性思考者];
    G --> H[最終回覆顯示於「AI對話記錄框」];

    subgraph "使用者操作"
        I[使用者可在「主席筆記區」隨時記錄]
        J[點擊「匯出對話紀錄」] --> K[觸發 file_handler];
        L[點擊「匯出主席筆記」] --> K;
        M[點擊「結束會議」] --> K;
    end

    K -- 生成檔案 --> N[[檔案系統: [主題]_[日期]_[類型].json]];
```

---

## 技術棧 (Tech Stack)

- **後端框架**: Python FastAPI
- **前端原型**: Python Gradio
- **AI 整合**: LangChain (`SequentialChain`)
- **相依性管理**: `requirements.txt`

---

## 檔案結構 (File Structure)

```
.
├── app.py              # Gradio 介面與 FastAPI 伺服器
├── core_logic.py       # LangChain AI 對話鏈邏輯
├── file_handler.py     # 檔案匯出功能
├── requirements.txt    # 專案相依性
└── outputs/            # 存放匯出的 JSON 檔案 (自動生成)
```

---

## 安裝與執行 (Setup & Run)

1.  **安裝相依性套件**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **執行應用程式**:
    ```bash
    python app.py
    ```
    應用程式將在本地啟動一個 Gradio 伺服器，可透過瀏覽器訪問。
