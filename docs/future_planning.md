# Multi-Agent System - Future Planning

This document provides a clear, systematic, and actionable technical roadmap for the future development of the AI-Collab-Chat project. The goal is to evolve the current "multi-role conversation system" into a true "multi-agent collaboration platform."

## Core Design Philosophy

1.  **Modularity and Scalability**: All new features should be designed in a modular way to ensure the system is easy to maintain and extend.
2.  **Prompt as Code**: Wherever possible, the behavior of the AI should be defined through well-designed prompts rather than being hardcoded. This gives the system maximum flexibility.
3.  **User-Centric**: All advanced features should be designed around giving the user greater control and a better user experience.

---

## Feature Evolution Roadmap

### Phase 1: Context Engineering

This is the cornerstone of achieving "true collaboration." The goal is to enable structured, lossless, and meaningful information transfer between agents.

*   **Current State**: Agents can only pass simple text responses to each other.
*   **Target State**: A subsequent agent can explicitly understand the "full output" of the previous agent, including its reasoning, conclusions, and suggested next steps.
*   **Technical Implementation**:
    1.  **Upgrade `Orchestrator`'s History Management**:
        *   Modify the data structure of the `history` log. When an agent with `output_parser: "json"` responds, store the **entire JSON object** (not just the `response` text) in the history.
        *   This JSON object can be considered a "Structured Context Node."
    2.  **Refine `ChatModule`'s Prompt Engineering**:
        *   Upgrade the `construct_prompt` function. When building a prompt for an agent, it will scan the history.
        *   If it finds a "Structured Context Node" from the previous turn, it will format this JSON object clearly and place it in a new `### Previous Task Output (Context) ###` section of the prompt.
        *   This allows the current agent to know exactly what "input" it is supposed to work on.

### Phase 2: Memory Summarization & Growth

The goal is to solve the problem of infinitely growing conversation histories and to lay the foundation for "long-term memory" and "self-improvement" for the agents.

*   **Current State**: Conversation history is saved and loaded in its entirety.
*   **Target State**:
    1.  Be able to **manually or automatically** compress a long conversation into a concise summary.
    2.  This summary can be used as "background knowledge" for new conversations, giving the agents long-term memory.
*   **Technical Implementation**:
    1.  **Add a `summarizer_bot`**:
        *   Create a new AI role specifically for summarization. Its prompt will be simple: "Condense the following conversation history into a brief summary."
    2.  **Add `summarize_memory()` to `Orchestrator`**:
        *   This method will read a specified history file and pass its content to the `summarizer_bot`.
        *   It will then save the summary to a new `.summary.txt` file, corresponding to the original `.json` history file.
    3.  **Add a Manual Trigger in `main.py`**:
        *   Add a "Manage Memory" option to the main menu.
        *   Users can select a history file and apply the "Summarize" action.
    4.  **Implement Summary Loading in `Orchestrator`**:
        *   When starting a new conversation, provide an option to load one or more summaries as "background knowledge," which will be placed in a `### Background Knowledge ###` section of the prompt.

### Phase 3: Tool Use / Function Calling

This is the key step to evolve the system from "chatting" to "executing tasks."

*   **Current State**: Agents can only generate text.
*   **Target State**: An agent can decide to call an external tool (e.g., web search, calculator, file I/O) and use the tool's output to formulate its final response.
*   **Technical Implementation**:
    1.  **Define a Tool Interface**: Create a `tools/` directory containing callable Python functions (e.g., `web_search.py`).
    2.  **Upgrade `ChatModule`'s Prompt Engineering**:
        *   Explicitly inform the AI in its prompt about the tools it can use, including their function and calling format.
        *   Instruct the AI to return a specific JSON format when it needs to use a tool, e.g., `{"tool_call": {"name": "web_search", "args": {"query": "AI market size"}}, "response": "I need to look up the current market size."}`
    3.  **Upgrade `Orchestrator`'s Conversation Loop**:
        *   In `run_conversation_loop`, check if the AI's response contains a `tool_call`.
        *   If so, pause the loop, execute the corresponding tool function.
        *   Pass the tool's execution result back to the **same AI** as a new conversation turn (`role: "tool_result"`), allowing it to generate a final response based on the new information.

### Phase 4: Advanced API Support

*   **Target State**: Create a more generic "Provider Framework" to make it easy to add support for other APIs like OpenAI, Anthropic, etc.
*   **Technical Implementation**:
    1.  Create a `providers/` directory.
    2.  Define an abstract `BaseProvider` class with standard interfaces like `generate_content` and `list_models`.
    3.  Create subclasses for Gemini, Ollama, OpenAI, etc., that inherit from `BaseProvider`.
    4.  The `ChatModule` will no longer call `genai` or `ollama` directly but will interact with the standardized Provider interface.

---

**Document Status**: Draft (v1.0)
**Planning Date**: 2025-09-28