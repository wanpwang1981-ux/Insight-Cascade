# AI-Collab-Chat: AI 協作對話系統

這是一個創新的 AI 互聊應用程式，旨在建立一個由多個獨立 AI 角色協同工作的對話系統。每個 AI 角色（模組）都可以擁有獨特的個性、設定和使用的 AI 模型。系統的核心目標是從一個單純的創意發想機器人，逐步演化成一個能夠分配具體任務、協同作業的強大平台。

## 核心功能

1.  **多模型供應商支援**:
    *   **Gemini API**: 支援 Google 的雲端 AI 模型。
    *   **Ollama**: 支援本地運行的開源模型（如 Llama3, Mistral 等）。
    *   可為每個 AI 角色**獨立配置**其使用的模型供應商和具體模型名稱。

2.  **智慧模型選擇**:
    *   **Ollama**: 自動偵測您本地已安裝的模型列表供您選擇。
    *   **Gemini/其他網路API**: 透過 `configs/models.json` 檔案，讓您手動管理一個乾淨、可用的模型列表，並可標記「我的最愛」使其優先顯示。

3.  **獨立聊天模組**:
    *   目前內建角色：
        *   `creative_bot_v1`: **領導型角色**。負責提出想法並動態決定下一步要交棒給誰。
        *   `analyst_bot_v1`: **終端型角色**。負責評估想法的可行性。
        *   `marketer_bot_v1`: **終端型角色**。負責包裝和宣傳想法。
        *   `model_scout_bot_v1`: **系統功能型角色**。一個特殊的工具人，負責查詢並回報當前環境所有可用的 Gemini 模型。

4.  **動態對話流程**:
    *   **使用者引導**: 在對話開始前，由使用者從可用角色列表和可用模型列表中，進行**雙重選擇**。
    *   **AI 協作**: 在對話過程中，**領導型角色**能動態決定下一個最適合接手對話的模組。
    *   **特殊動作**: 選擇**系統功能型角色**時，會直接執行特定系統任務，而非進行對話。

5.  **對話記憶系統**:
    *   對話結束後，完整的、帶時間戳的歷史紀錄會自動儲存到 `memory/` 資料夾。
    *   程式啟動時，可選擇載入舊記憶，並在該上下文中繼續對話。

## 如何管理您的模型列表 (`models.json`)

為了避免 API 回傳過長或包含無法使用的模型列表，我們採用一個手動維護的 `configs/models.json` 檔案來管理網路 API 模型。

您可以編輯此檔案，只留下您確定可用且偏好的模型。

*   **provider**: `gemini` 或未來支援的 `openai` 等。
*   **name**: 模型的確切名稱。
*   **is_favorite**: 設為 `true` 的模型，會在選擇列表中被優先顯示。

```json
{
  "gemini": [
    { "name": "gemini-1.5-pro", "is_favorite": true },
    { "name": "gemini-pro", "is_favorite": false }
  ],
  "openai": [
    { "name": "gpt-4o", "is_favorite": true }
  ]
}
```

## 安裝與設定

### 1. 複製專案庫
```bash
git clone <your-repository-url>
cd <repository-folder>
```

### 2. 設定環境變數
1.  在專案的根目錄下，將 `.env.example` 檔案複製並重新命名為 `.env`。
2.  用您的文字編輯器打開 `.env` 檔案，並填入您需要的變數。
    *   若要使用 Gemini，必須填寫 `GEMINI_API_KEY`。
    *   若您的 Ollama 不在本機，請填寫 `OLLAMA_HOST`。

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

2.  **第一步：選擇 AI 角色**
    程式啟動後，會顯示所有可用的 AI 角色列表。請依照提示輸入數字，選擇您希望由哪個角色開啟對話。
    ```
    請選擇一個起始 AI 角色來開始對話：
      1: analyst_bot_v1
      2: creative_bot_v1
      3: marketer_bot_v1
    請輸入選項 (1-3): [在此處輸入您的選擇]
    ```

3.  **第二步：選擇對話模型**
    選擇角色後，程式會**動態查詢**該角色供應商（目前僅支援 Gemini）所有可用的模型。如果查詢到多個模型，會再次請您選擇。
    ```
    請為 'creative_bot_v1' 選擇要使用的模型：
      1: gemini-1.5-pro
      2: gemini-1.5-flash-lite
      3: gemini-pro
    請輸入選項 (1-3): [在此處輸入您的選擇]
    ```
    *(如果該角色使用 Ollama，或 Gemini 模型只有一個可用，程式會自動選擇預設模型並跳過此步驟。)*

4.  **第三步：輸入對話主題**
    完成雙重選擇後，程式會提示您輸入對話的主題。
    ```
    請輸入一個主題來開始對話: [在此處輸入您的主題]
    ```

## 如何設定一個 Ollama 模組
您可以輕易地將任何一個 AI 角色切換為使用本地的 Ollama 模型。

1.  **安裝並執行 Ollama**: 請先確保您已依照 [Ollama 官方指南](https://ollama.com/) 安裝了 Ollama，並已下載您想使用的模型（例如 `ollama run llama3`）。

2.  **修改設定檔**: 打開您想修改的角色的 `.json` 設定檔（例如 `configs/modules/analyst_bot.json`）。將 `model` 物件修改如下：
    ```json
    "model": {
        "provider": "ollama",
        "name": "llama3"
    }
    ```
    *   `provider`: 必須設為 `"ollama"`。
    *   `name`: 設為您已經在本地下載好的模型名稱。

3.  **(可選) 設定 Ollama 主機**: 如果您的 Ollama 服務不是在本機執行，請在您的 `.env` 檔案中設定 `OLLAMA_HOST` 變數。

## 常見問題
**Q: 程式執行後，AI 沒有回應，或是出現關於「安全機制」的錯誤訊息。**

**A:** 這是正常的。大型語言模型（如 Gemini）的供應商通常會內建內容安全審核機制。有時候，即使是無害的提示或預期的回覆，也可能觸發這個機制，導致 API 拒絕生成內容。我們的程式已經加入了偵測這種情況的功能。如果遇到這種狀況，請嘗試**換個方式提問**或**修改您的主題**，通常就能解決問題。

## 版本管理

| 版本 | 日期 | 主要變更 |
| :--- | :--- | :--- |
| **v0.6.0** | 2025-09-28 | - **新增「模型偵察兵」**：一個特殊的系統功能角色，用於查詢可用模型。<br>- **優化 `main.py`**：為特殊動作角色提供了一鍵式的便捷操作流程。 |
| v0.5.0 | 2025-09-28 | - **新增智慧模型選擇**：改為從 `models.json` 讀取網路模型，並支援我的最愛排序。<br>- **新增 Ollama 模型列表**：實現動態獲取本地 Ollama 模型的功能。<br>- **修正 `AttributeError`**：徹底修正因重構不全導致的程式崩潰問題。<br>- **補全文件**：建立 `future_planning.md` 並更新 `readme.md`。 |
| v0.4.0 | 2025-09-28 | - **新增對話記憶系統**：實現了對話歷史的儲存與載入功能。<br>- **新增動態模型偵測**：`ChatModule` 能動態查詢 Gemini 的可用模型。<br>- **重構 `main.py`**：實現了雙重選擇流程（角色 -> 模型）。<br>- **修正 `AttributeError`**：修復了因 `safety_settings` 導致的程式崩潰。 |
| v0.3.0 | 2025-09-24 | - **實現動態多角色對話**：賦予 `creative_bot` 領導能力。<br>- **新增 `marketer_bot`**：擴充 AI 團隊角色。<br>- **強化 API 回應處理**：能處理安全機制攔截。 |
| v0.2.0 | 2025-09-23 | - **串接 Google Gemini API**：實現了從模擬回應到真實 AI 的轉換。<br>- **新增相依套件**：加入 `google-generativeai` 和 `python-dotenv`。<br>- **新增 `.env` 環境變數管理**。 |
| v0.1.0 | 2025-09-23 | - **專案初始化**：建立核心架構與基礎文件 (`readme.md`, `system_architecture.md`)。 |