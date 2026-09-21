"""State schema for Cairo Care LangGraph agent."""
from typing import Annotated
from typing_extensions import TypedDict

try:
    from langgraph.graph.message import add_messages
except ImportError:
    def add_messages(left: list, right: list) -> list:
        return left + right


# ── Reducers ──────────────────────────────────────────────────────────────────

def merge_doctors(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge incoming doctors, deduplicating by profile_url."""
    seen_urls: set[str] = {doc.get("profile_url", "") for doc in existing}
    unique_new = [doc for doc in new if doc.get("profile_url", "") not in seen_urls]
    return existing + unique_new


def merge_hospitals(existing: list[dict], new: list[dict]) -> list[dict]:
    """Merge incoming hospitals, deduplicating by name."""
    seen_names: set[str] = {h.get("name", "") for h in existing}
    unique_new = [h for h in new if h.get("name", "") not in seen_names]
    return existing + unique_new


# ── State schema ──────────────────────────────────────────────────────────────

class CairoState(TypedDict):
    """
    Cairo Care LangGraph agent state.
    """
    messages:  Annotated[list, add_messages]
    doctors:   Annotated[list[dict], merge_doctors]
    hospitals: Annotated[list[dict], merge_hospitals]
    query:     str
