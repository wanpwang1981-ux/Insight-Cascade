import os
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain

# --- 預設提示詞模板 ---
DEFAULT_ANALYST_TEMPLATE = """
作為一位專業的文件分析師，你的任務是從使用者提供的問題中，提取關鍵資訊和潛在的數據點。
專注於客觀事實，避免主觀臆測。你的分析將作為後續創意發想的基礎。
使用者問題: {question}
你的分析:
"""

DEFAULT_STRATEGIST_TEMPLATE = """
作為一位充滿想像力的創意策略師，你的任務是基於文件分析師的客觀分析，提出三個創新且可行的解決方案或點子。
思考要發散，但不能脫離現實。
分析師的結論:
{analysis}
你的三個創意策略:
1. ...
2. ...
3. ...
"""

DEFAULT_CRITIC_TEMPLATE = """
作為一位嚴謹的批判性思考者，你的任務是評估創意策略師提出的方案。
請從風險、成本、可行性三個角度，逐一分析每個策略的潛在問題，並給出最終的綜合建議。
創意策略:
{strategies}
你的批判性評估:
- 策略一:
  - 風險: ...
  - 成本: ...
  - 可行性: ...
- 策略二:
  ...
- 策略三:
  ...
綜合建議:
...
"""

def run_main_chain(question: str, roles: list) -> dict:
    """
    根據動態的角色列表，建立並執行一個多供應商的循序 AI 鏈。

    Args:
        question (str): 使用者提出的問題。
        roles (list): 一個包含多個角色設定字典的列表。

    Returns:
        dict: 包含所有 AI 專家產出的字典，或在出錯時返回錯誤訊息。
    """
    chains = []
    output_keys = []

    try:
        for i, role in enumerate(roles):
            role_name = role.get("name", f"角色 {i+1}")
            provider = role.get("provider", "Ollama")
            prompt_template_str = role.get("prompt", "請回答： {input}")

            # --- 動態選擇並初始化 LLM ---
            if provider == "Ollama":
                model_name = role.get("model_name", "llama3")
                try:
                    llm = Ollama(model=model_name)
                except Exception as e:
                    raise Exception(f"角色 '{role_name}' 的 Ollama 模型 '{model_name}' 連接失敗: {e}")

            elif provider == "Gemini":
                api_key = role.get("api_key")
                if not api_key:
                    raise ValueError(f"角色 '{role_name}' 已選擇 Gemini，但未提供 API 金鑰。")
                try:
                    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key,
                                                 convert_system_message_to_human=True)
                except Exception as e:
                    raise Exception(f"角色 '{role_name}' 的 Gemini 模型連接失敗: {e}")
            else:
                raise ValueError(f"角色 '{role_name}' 的 AI 提供商 '{provider}' 不被支援。")

            # --- 動態建立 Prompt 和 Chain ---
            # 決定輸入變數
            if i == 0:
                input_variables = ["question"]
            else:
                # 前一個鏈的輸出是下一個鏈的輸入
                prev_output_key = output_keys[i-1]
                input_variables = [prev_output_key]

            # 為本鏈定義輸出變數
            current_output_key = f"output_{i+1}_{role_name.replace(' ', '_').lower()}"
            output_keys.append(current_output_key)

            prompt = PromptTemplate(template=prompt_template_str, input_variables=input_variables)
            chain = LLMChain(llm=llm, prompt=prompt, output_key=current_output_key)
            chains.append(chain)

        if not chains:
            return {"error": "沒有可執行的 AI 角色。"}

        # --- 整合為循序鏈 ---
        main_chain = SequentialChain(
            chains=chains,
            input_variables=["question"],
            output_variables=output_keys,
            verbose=True
        )

        # 執行鏈並獲得結果
        result = main_chain({"question": question})
        return result

    except Exception as e:
        print(f"執行 LangChain 時發生錯誤: {e}")
        return {"error": str(e)}

if __name__ == '__main__':
    # 用於單元測試的範例
    print("執行 core_logic.py 單元測試...")
    test_question = "如何提升我們 App 在下一季的用戶留存率？"

    # 準備預設的提示詞進行測試
    mock_prompts = {
        "global": "這是一個測試。",
        "analyst": DEFAULT_ANALYST_TEMPLATE,
        "strategist": DEFAULT_STRATEGIST_TEMPLATE,
        "critic": DEFAULT_CRITIC_TEMPLATE,
    }

    print("\n--- 警告 ---")
    print("此測試會嘗試連接您在本地運行的 Ollama 服務。")
    print("請確保 Ollama 已安裝並正在運行，且模型 'llama3' 已拉取。")
    print("若要更改測試模型，請修改此腳本中的 'test_model' 變數。")
    print("--------------")

    test_model = "llama3"
    output = run_main_chain(test_question, test_model, mock_prompts)

    print("\n--- 測試輸入 ---")
    print(f"問題: {test_question}")

    print("\n--- 測試輸出 ---")
    for key, value in output.items():
        print(f"[{key.upper()}]\n{value}\n")

    print("單元測試結束。")
