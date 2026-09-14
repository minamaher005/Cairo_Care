"""
Cairo Care — RAG Agent
======================

Answers questions about Cairo hospitals by retrieving relevant records from Qdrant
and generating responses with an Ollama LLM.

Usage:
    python agent.py "ايش مستشفيات القلب في القاهرة؟"
"""

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from config import OLLAMA_BASE_URL, OLLAMA_LLM_MODEL
from vector_store import get_vector_store


# ── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are Cairo Care, a helpful assistant for hospital information in Cairo, Egypt.

## Instructions
- Answer questions **in Arabic** using only the hospital data retrieved from the database.
- If the retrieved results do not contain enough information to answer, say that clearly — do not make up hospitals, phone numbers, or addresses.
- When listing hospitals, include their name, address, specialty, and phone number if available.
- Be concise and organized. Use bullet points when listing multiple hospitals.
"""


# ── Retrieval tool ───────────────────────────────────────────────────────────
@tool
def search_hospitals(query: str) -> str:
    """Search the Cairo hospital database for records relevant to the query.

    Args:
        query: The user's question or keywords, in Arabic or English.
    """
    vector_store = get_vector_store()

    # Retrieve the top-5 most similar hospital documents
    results = vector_store.similarity_search(query, k=5)

    if not results:
        return "No hospitals found matching this query."

    # Format each result as a readable block
    blocks = []
    for i, doc in enumerate(results, start=1):
        meta = doc.metadata
        blocks.append(
            f"{i}. **{meta.get('name', 'N/A')}**\n"
            f"   العنوان: {meta.get('address', 'N/A')}\n"
            f"   التخصص: {meta.get('specialty', 'N/A')}\n"
            f"   الهاتف: {meta.get('phone', 'N/A')}\n"
            f"   الموقع: {meta.get('website', 'N/A')}"
        )

    return "\n\n".join(blocks)


# ── Agent factory ────────────────────────────────────────────────────────────
def create_cairo_care_agent():
    """Build and return the Cairo Care RAG agent.

    The agent uses an Ollama LLM, a Qdrant-backed retrieval tool, and
    in-memory conversation history for multi-turn chat.
    """
    # Initialize the LLM from config values (ollama:model_name)
    llm = init_chat_model(
        model=OLLAMA_LLM_MODEL,
        temperature=0,
        base_url=OLLAMA_BASE_URL,
    )

    # In-memory checkpointer so the agent remembers conversation threads
    checkpointer = InMemorySaver()

    # Assemble the agent: model + tools + system prompt + memory
    agent = create_agent(
        model=llm,
        tools=[search_hospitals],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


# ── CLI entry point ──────────────────────────────────────────────────────────
def main():
    """Run an interactive chat loop."""
    import sys

    # If a question was passed as a command-line argument, answer once and exit.
    if len(sys.argv) > 1:
        user_question = " ".join(sys.argv[1:])
        agent = create_cairo_care_agent()

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_question}]},
            config={"configurable": {"thread_id": "cli-session"}},
        )

        # Extract the final text from the agent's response
        last_message = result["messages"][-1]
        print(last_message.content)
        return

    # Otherwise, start an interactive loop.
    print("=" * 60)
    print("Cairo Care — Hospital Information Assistant")
    print('Type "quit" or "exit" to leave.')
    print("=" * 60)

    agent = create_cairo_care_agent()
    thread_id = 0

    while True:
        user_question = input("\nYou: ").strip()

        if user_question.lower() in ("quit", "exit", "خروج"):
            print("Goodbye!")
            break

        thread_id += 1
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_question}]},
            config={"configurable": {"thread_id": f"interactive-{thread_id}"}},
        )

        last_message = result["messages"][-1]
        print(f"\nCairo Care: {last_message.content}")


if __name__ == "__main__":
    main()
