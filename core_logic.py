import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from dotenv import load_dotenv

# 載入環境變數 (例如 OPENAI_API_KEY)
load_dotenv()

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

def run_main_chain(question: str, custom_prompts: dict) -> dict:
    """
    執行主要的 AI 對話鏈。
    如果未設定 OPENAI_API_KEY，則返回模擬回應。
    否則，使用提供的提示詞動態建立並執行 LangChain。

    Args:
        question (str): 使用者提出的問題。
        custom_prompts (dict): 包含 'analyst', 'strategist', 'critic' 提示詞的字典。

    Returns:
        dict: 包含所有 AI 專家產出的字典。
    """
    if not os.getenv("OPENAI_API_KEY"):
        # 在沒有 API Key 的情況下返回一個模擬的回應，方便前端測試
        return {
            "analysis": "模擬分析：問題的關鍵在於提升使用者參與度。",
            "strategies": "模擬策略：1. 遊戲化 2. 社群功能 3. 個人化推薦。",
            "critique": "模擬批判：遊戲化成本高，社群功能需要長時間經營，個人化推薦是最佳起點。"
        }

    try:
        # --- 動態初始化 LLM 和 Chains ---
        llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")

        # 結合全域提示詞與分析師提示詞
        global_prompt = custom_prompts.get("global", "")
        analyst_template = global_prompt + "\n\n" + custom_prompts.get("analyst", DEFAULT_ANALYST_TEMPLATE)

        # 1. 分析師
        analyst_prompt = PromptTemplate(input_variables=["question"], template=analyst_template)
        analyst_chain = LLMChain(llm=llm, prompt=analyst_prompt, output_key="analysis")

        # 2. 策略師
        strategist_template = custom_prompts.get("strategist", DEFAULT_STRATEGIST_TEMPLATE)
        strategist_prompt = PromptTemplate(input_variables=["analysis"], template=strategist_template)
        strategist_chain = LLMChain(llm=llm, prompt=strategist_prompt, output_key="strategies")

        # 3. 批判者
        critic_template = custom_prompts.get("critic", DEFAULT_CRITIC_TEMPLATE)
        critic_prompt = PromptTemplate(input_variables=["strategies"], template=critic_template)
        critic_chain = LLMChain(llm=llm, prompt=critic_prompt, output_key="critique")

        # 整合為循序鏈
        main_chain = SequentialChain(
            chains=[analyst_chain, strategist_chain, critic_chain],
            input_variables=["question"],
            output_variables=["analysis", "strategies", "critique"],
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

    # 檢查 API Key 是否存在
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未找到 OPENAI_API_KEY 環境變數。將使用模擬回應。")
        print("若要進行真實測試，請在 .env 檔案中設定 OPENAI_API_KEY=your_key")

    output = run_main_chain(test_question)

    print("\n--- 測試輸入 ---")
    print(f"問題: {test_question}")

    print("\n--- 測試輸出 ---")
    for key, value in output.items():
        print(f"[{key.upper()}]\n{value}\n")

    print("單元測試結束。")
