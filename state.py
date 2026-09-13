"""
state.py
--------
LangGraph state schema for the Cairo Care agent.

الاستخدام:
    from Cairo_Care.state import CairoState, merge_doctors

    # إنشاء state فاضي
    state: CairoState = {"messages": [], "doctors": [], "query": ""}

    # دمج نتائج جديدة في قائمة الدكاترة
    new_doctors = search_vezeeta_doctors.invoke(...)
    state["doctors"] = merge_doctors(state["doctors"], new_doctors)
"""

from typing import Annotated, Any
from typing_extensions import TypedDict

try:
    from langgraph.graph.message import add_messages
except ImportError:  # fallback لو langgraph مش متاح
    def add_messages(left: list, right: list) -> list:  # type: ignore[misc]
        return left + right


# ---------------------------------------------------------------------------
# Reducer: بيجمع نتائج الدكاترة من أكتر من استدعاء للـ tool
# ---------------------------------------------------------------------------

def merge_doctors(existing: list[dict], new: list[dict]) -> list[dict]:
    """
    يضم نتائج جديدة لقائمة الدكاترة الموجودة.

    - بيتجنب التكرار بناءً على profile_url
    - بيحتفظ بالترتيب (القديم الأول)
    """
    seen_urls: set[str] = {doc.get("profile_url", "") for doc in existing}
    unique_new = [doc for doc in new if doc.get("profile_url", "") not in seen_urls]
    return existing + unique_new


# ---------------------------------------------------------------------------
# CairoState — الـ TypedDict الرئيسي للـ LangGraph state
# ---------------------------------------------------------------------------

class CairoState(TypedDict):
    """
    State للـ Cairo Care LangGraph agent.

    الحقول:
        messages: سجل المحادثة (يُدار بـ add_messages reducer من LangGraph)
        doctors:  قائمة دكاترة مجمّعة من استدعاءات الـ tool
                  كل عنصر dict يحتوي: name, title, description, fees,
                  rating, ratings_count, address, profile_url, sponsored
        query:    آخر سؤال المستخدم (للرجوع إليه في أي node)
    """
    messages: Annotated[list, add_messages]
    doctors:  Annotated[list[dict], merge_doctors]
    hospitals: Annotated[list[dict], add_messages]
    query:    str



