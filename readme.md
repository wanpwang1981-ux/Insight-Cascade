# AI-Collab-Chat: AI 協作對話系統

這是一個創新的 AI 互聊應用程式，旨在建立一個由多個獨立 AI 角色協同工作的對話系統。每個 AI 角色（模組）都可以擁有獨特的個性、設定和使用的 AI 模型。系統的核心目標是從一個單純的創意發想機器人，逐步演化成一個能夠分配具體任務、協同作業的強大平台。

## 核心功能

1.  **獨立聊天模組**:
    *   可以為每個 AI 角色進行獨立的設定（例如：角色背景、說話風格）。
    *   支援多種 AI 模型接入（例如：本地模型、Gemini API、或其他第三方服務）。
    *   提供單元測試功能，確保每個模組的個性符合設計預期。

2.  **無限擴展性**:
    *   系統設計允許無限增加新的 AI 聊天模組。

3.  **可編排的對話流程**:
    *   使用者給定一個初始主題後，第一個 AI 模組會進行回應。
    *   該模組在完成思考後，可以根據預設邏輯或動態判斷，將對話指派給下一個（或多個）AI 模組接力處理。

4.  **等候與同步機制**:
    *   系統將確保在一個 AI 模組完成其發言之前，下一個模組會處於等候狀態，確保對話的有序性。

## 安裝與設定

### 1. 複製專案庫
```bash
git clone <your-repository-url>
cd <repository-folder>
```

### 2. 設定 API 金鑰
為了讓 AI 能夠真正運作，您需要一個 Google Gemini API 金鑰。

1.  從 [Google AI Studio](https://aistudio.google.com/) 取得您的 API 金鑰。
2.  在專案的根目錄下，將 `.env.example` 檔案複製並重新命名為 `.env`。
3.  用您的文字編輯器打開 `.env` 檔案，並將您的 API 金鑰貼入其中：
    ```env
    GEMINI_API_KEY="在這裡貼上您自己的API金鑰"
    ```

### 3. 建立並啟用虛擬環境 (建議)
您可以選擇使用傳統的 `venv` 或是更快速的 `uv`。

<details>
<summary><strong>選項 A: 使用 `venv` (Python 內建)</strong></summary>

```bash
# 建立虛擬環境 (在 Windows 上請使用 python)
python -m venv .venv

# 啟用虛擬環境
# - macOS / Linux:
source .venv/bin/activate
# - Windows:
.venv\Scripts\activate
```
</details>

<details>
<summary><strong>選項 B: 使用 `uv` (推薦，更快速)</strong></summary>

首先，請確保您已安裝 `uv`。若未安裝，請參考 [uv 官方安裝指南](https://docs.astral.sh/uv/install/)。

```bash
# 建立虛擬環境
uv venv

# 啟用虛擬環境
# - macOS / Linux:
source .venv/bin/activate
# - Windows:
.venv\Scripts\activate
```
</details>

### 4. 安裝相依套件
根據您選擇的工具，執行以下任一指令：

```bash
# 如果您使用 venv + pip
pip install -r requirements.txt

# 如果您使用 uv
uv pip install -r requirements.txt
```

## 操作說明

1.  **執行應用程式**
    在專案根目錄下，執行以下指令。
    *(註：根據您的系統設定，您可能需要使用 `python3` 而非 `python`)*
    ```bash
    python main.py
    ```

2.  **開始對話**
    程式啟動後，會提示您輸入一個主題。輸入您想討論的主題後按下 Enter，AI 就會開始對話。
    ```
    請輸入一個主題來開始對話: [在此處輸入您的主題]
    ```

## 專案演進藍圖

*   **階段一：創意發想機器人** - 實現核心的單一 AI 模組對話功能。
*   **階段二：真實 AI 串接** - 引入真實 AI 模型 (Gemini) 並處理 API 金鑰。
*   **階段三：多角色對話** - 引入多個 AI 模組，並實現基本的對話接力功能。

## 版本管理

| 版本  | 日期       | 主要變更                                       |
| :---- | :--------- | :--------------------------------------------- |
| v0.2.0| YYYY-MM-DD | - 串接 Google Gemini API<br>- 新增 `python-dotenv` 和 `google-generativeai` 套件<br>- 更新 `readme.md` 的 API 金鑰設定說明 |
| v0.1.0| YYYY-MM-DD | - 專案初始化<br>- 建立 `readme.md` 和系統架構分析文件。 |
