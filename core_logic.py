import os
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain

# --- 預設提示詞模板 ---
DEFAULT_ANALYST_TEMPLATE = """任務：作為文件分析師，從問題中提取關鍵資訊和數據點。專注於客觀事實。
問題：{question}
你的分析："""

DEFAULT_STRATEGIST_TEMPLATE = """任務：作為創意策略師，基於以下分析，提出三個創新且可行的解決方案。
分析師的結論：
{analysis}
你的三個創意策略："""

DEFAULT_CRITIC_TEMPLATE = """任務：作為批判性思考者，評估以下策略的風險、成本和可行性，並給出綜合建議。
創意策略：
{strategies}
你的批判性評估："""

def run_main_chain(question: str, roles: list) -> dict:
    """
    根據動態的角色列表，建立並執行一個多供應商的循序 AI 鏈。
    Args:
        question (str): 使用者提出的問題。
        roles (list): 一個包含多個角色設定字典的列表。
    Returns:
        dict: 包含所有 AI 專家產出的字典，或在出錯時返回錯誤訊息。
    """
    try:
        if len(roles) != 3:
            raise ValueError("此版本的核心邏輯需要剛好 3 個角色。")

        # 定義固定的輸入/輸出鍵，以確保鏈的正確連接
        chain_keys = [
            {"input": "question", "output": "analysis"},
            {"input": "analysis", "output": "strategies"},
            {"input": "strategies", "output": "critique"}
        ]

        chains = []
        for i, role in enumerate(roles):
            role_name = role.get("name", f"角色 {i+1}")
            provider = role.get("provider", "Ollama")
            prompt_template_str = role.get("prompt")

            # --- 動態選擇並初始化 LLM ---
            if provider == "Ollama":
                model_name = role.get("model_name", "llama3")
                try:
                    llm = Ollama(model=model_name)
                except Exception as e:
                    raise Exception(f"角色 '{role_name}' (Ollama) 連接失敗: {e}")
            elif provider == "Gemini":
                api_key = role.get("api_key")
                if not api_key:
                    raise ValueError(f"角色 '{role_name}' (Gemini) 未提供 API 金鑰。")
                try:
                    llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key, convert_system_message_to_human=True)
                except Exception as e:
                    raise Exception(f"角色 '{role_name}' (Gemini) 連接失敗: {e}")
            else:
                raise ValueError(f"角色 '{role_name}' 的 AI 提供商 '{provider}' 不被支援。")

            # --- 建立 Prompt 和 Chain ---
            input_key = chain_keys[i]["input"]
            output_key = chain_keys[i]["output"]

            # 驗證模板是否包含必要的輸入變數
            if f"{{{input_key}}}" not in prompt_template_str:
                raise ValueError(f"角色 '{role_name}' 的提示詞模板缺少必要的輸入變數 `{{{input_key}}}`。")

            prompt = PromptTemplate(template=prompt_template_str, input_variables=[input_key])
            chain = LLMChain(llm=llm, prompt=prompt, output_key=output_key)
            chains.append(chain)

        # --- 整合為循序鏈 ---
        main_chain = SequentialChain(
            chains=chains,
            input_variables=["question"],
            output_variables=[key["output"] for key in chain_keys],
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

    mock_roles_test = [
        {"name": "分析師", "provider": "Ollama", "model_name": "llama3", "prompt": DEFAULT_ANALYST_TEMPLATE},
        {"name": "策略師", "provider": "Ollama", "model_name": "llama3", "prompt": DEFAULT_STRATEGIST_TEMPLATE},
        {"name": "批判者", "provider": "Ollama", "model_name": "llama3", "prompt": DEFAULT_CRITIC_TEMPLATE}
    ]

    print("\n--- 警告 ---")
    print("此測試會嘗試連接您在本地運行的 Ollama 服務。")
    print("請確保 Ollama 已安裝並正在運行，且模型 'llama3' 已拉取。")
    print("--------------")

    output = run_main_chain(test_question, mock_roles_test)

    print("\n--- 測試輸入 ---")
    print(f"問題: {test_question}")

    print("\n--- 測試輸出 ---")
    if "error" in output:
        print(f"測試失敗，出現錯誤: {output['error']}")
    else:
        print(f"[ANALYSIS]: {output.get('analysis')}")
        print(f"[STRATEGIES]: {output.get('strategies')}")
        print(f"[CRITIQUE]: {output.get('critique')}")
        if all(k in output for k in ["analysis", "strategies", "critique"]):
            print("\n測試成功：所有預期的輸出鍵都已找到。")
        else:
            print("\n測試失敗：缺少部分輸出鍵。")

    print("\n單元測試結束。")

def test_gemini_api_key(api_key: str) -> str:
    """
    測試給定的 Gemini API 金鑰是否有效。
    """
    if not api_key:
        return "❌ 錯誤：API 金鑰不能為空。"
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
        # 嘗試一個非常簡單的操作來觸發驗證，例如獲取模型資訊
        llm.get_num_tokens("test")
        return "✅ 金鑰驗證成功！"
    except Exception as e:
        # 捕獲所有可能的錯誤，包括認證失敗、網路問題等
        return f"❌ 金鑰驗證失敗: {str(e)}"
