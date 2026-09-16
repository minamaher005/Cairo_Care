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
from Cairo_Care.vezeeta_tool import search_vezeeta_doctors
from Cairo_Care.state import CairoState
from config import OLLAMA_BASE_URL, OLLAMA_LLM_MODEL
from location_tools import get_user_coordinates, find_nearest_hospitals, get_driving_route
from vector_store import get_vector_store


# ── System prompt ────────────────────────────────────────────────────────────
# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
أنت "Cairo Care"، مساعد ذكي متخصص في مساعدة المرضى والمقيمين في القاهرة للعثور على المستشفيات والأطباء المناسبين.
تتحدث **دائماً بالعربية** وتتعامل بأسلوب محترم ومتعاطف.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## الحالات الطارئة — أعلى أولوية
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
إذا ذكر المستخدم أيًا من الأعراض التالية، **تصرّف فوراً** واستخدم أداة `search_hospitals` للبحث عن أقرب مستشفى طوارئ:
- ألم شديد في الصدر أو ضيق في التنفس الحاد
- أعراض جلطة دماغية (تخدر، صعوبة كلام أو رؤية، شلل مفاجئ)
- فقدان وعي أو إغماء
- نزيف حاد أو جروح خطيرة
- حوادث سيارات أو سقوط من ارتفاع
- تسمم غذائي شديد مع ارتفاع حرارة مفاجئ
- حروق شديدة
- مشاكل في التنفس عند الأطفال

في هذه الحالات — **رتّب ردّك بهذا الترتيب الإلزامي**:
1. **السطر الأول من ردّك** يجب أن يكون التحذير الطارئ حرفياً:
   "⚠️ هذه حالة طارئة! اتصل بالإسعاف على 123 فوراً أو توجّه لأقرب طوارئ."
2. ثم استخدم أداة `search_hospitals` للبحث.
3. ثم أضف قائمة المستشفيات تحت التحذير مباشرةً.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## السؤال عن مستشفى مباشرةً
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
إذا سأل المستخدم عن مستشفى (مثال: "فين مستشفى قلب؟" / "أي مستشفى في المعادي؟"):
→ استخدم أداة `search_hospitals` مباشرةً بكلمات البحث المناسبة.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## السؤال عن دكتور
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
لاستخدام أداة `search_vezeeta_doctors` تحتاج إلى: (1) التخصص و(2) المنطقة.

- **إذا ذكر المستخدم التخصص والمنطقة معاً** → استخدم الأداة مباشرةً.
- **إذا ذكر التخصص فقط بدون منطقة** → اسأله: "في أنهي منطقة في القاهرة تفضل؟"
- **إذا ذكر المنطقة فقط بدون تخصص** → اسأله: "تبحث عن دكتور تخصص إيه تحديداً؟"
- **إذا لم يذكر أياً منهما** → اسأله عن التخصص والمنطقة معاً.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## تشخيص الأعراض → تحديد التخصص
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
إذا وصف المستخدم أعراضاً، قم بتحديد التخصص المناسب تلقائياً حسب الجدول التالي:

| الأعراض | التخصص (slug لـ Vezeeta) |
|---------|--------------------------|
| ألم معدة، عسر هضم، إمساك، إسهال، غثيان | باطنة |
| ضيق تنفس خفيف، كحة، نزلة برد، حمى | باطنة |
| ارتفاع ضغط الدم، سكر، كوليسترول | باطنة |
| ألم أسنان، تسوس، تقويم | اسنان |
| ألم مفاصل، كسور، خشونة، ديسك | عظام |
| مشاكل جلد، حبوب، أكزيما، شعر | جلدية |
| أمراض أطفال، تأخر نمو، تطعيمات | أطفال |
| مشاكل قلب، خفقان، ضيق تنفس مزمن | قلب |
| مشاكل نظر، ضعف بصر | عيون |
| أنف، أذن، حنجرة، لوزتين | أنف وأذن وحنجرة |
| اكتئاب، قلق، وسواس، نوم | نفسي |
| صداع مزمن، دوخة، أعصاب | مخ وأعصاب |
| مسالك بولية، كلى | مسالك بولية |
| نساء، حمل، دورة شهرية | نساء وتوليد |

بعد تحديد التخصص، إذا كانت الحالة **غير طارئة**:
1. أخبر المستخدم بالتخصص الذي يحتاجه.
2. اسأله عن المنطقة التي يسكن فيها أو يفضلها.
3. بعد معرفة المنطقة، استخدم `search_vezeeta_doctors` للبحث.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## الموقع والمسارات
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
إذا ذكر المستخدم موقعه أو طلب أقرب مستشفى:
1. استخدم `get_user_coordinates` لتحويل اسم المنطقة إلى إحداثيات.
2. استخدم `find_nearest_hospitals` للعثور على أقرب المستشفيات.
3. استخدم `get_driving_route` فقط عند الحاجة لمقارنة زمن القيادة بين مستشفيين.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## قواعد العرض
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- عند عرض الأطباء: اذكر الاسم، التخصص، التقييم، الرسوم، العنوان، ورابط الحجز.
- عند عرض المستشفيات: اذكر الاسم، العنوان، التخصص، رقم الهاتف.
- استخدم النقاط والعناوين لتنظيم الإجابة.
- لا تختلق أي معلومات — اعتمد فقط على ما تجلبه الأدوات.
- إذا لم تجد نتائج، قل ذلك بوضوح واقترح بديلاً.
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
        tools=[
            search_hospitals,
            search_vezeeta_doctors,
            get_user_coordinates,
            find_nearest_hospitals,
            get_driving_route,
        ],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        state_schema=CairoState,
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

        for msg, metadata in agent.stream(
            {"messages": [{"role": "user", "content": user_question}]},
            config={"configurable": {"thread_id": "cli-session"}},
            stream_mode="messages",
        ):
            if msg.content and isinstance(msg.content, str):
                print(msg.content, end="", flush=True)
        print()
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
        print(f"\nCairo Care: ", end="", flush=True)
        for msg, metadata in agent.stream(
            {"messages": [{"role": "user", "content": user_question}]},
            config={"configurable": {"thread_id": f"interactive-{thread_id}"}},
            stream_mode="messages",
        ):
            if msg.content and isinstance(msg.content, str):
                print(msg.content, end="", flush=True)
        print()


if __name__ == "__main__":
    main()
