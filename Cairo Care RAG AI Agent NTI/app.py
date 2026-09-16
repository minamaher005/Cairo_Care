














"""
الملف يستدعي create_cairo_care_agent من agent.py
"""

import uuid
import html

import streamlit as st


try:
    from agent import create_cairo_care_agent

    AGENT_AVAILABLE = True
    AGENT_IMPORT_ERROR = None

except Exception as e:
    AGENT_AVAILABLE = False
    AGENT_IMPORT_ERROR = str(e)




st.set_page_config(
    page_title="Cairo Care",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)



CUSTOM_CSS = """
<style>

:root {
    --cc-navy: #0b3d66;
    --cc-blue: #1a6fb0;
    --cc-blue-light: #4f9fd8;
    --cc-blue-pale: #eaf4fb;
    --cc-blue-paler: #f5fafd;
    --cc-white: #ffffff;
    --cc-gray: #5b7286;
    --cc-text: #1a2733;
}




html,
body,
[class*="css"] {
    font-family: "Tahoma", "Segoe UI", sans-serif;
}




.stApp {
    background: linear-gradient(
        180deg,
        var(--cc-blue-paler) 0%,
        var(--cc-white) 55%
    );
}

[data-testid="stAppViewContainer"] {
    background: var(--cc-blue-paler) !important;
}

[data-testid="stMain"] {
    background: transparent !important;
}



[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        var(--cc-navy) 0%,
        var(--cc-blue) 100%
    );
}

[data-testid="stSidebar"] * {
    color: var(--cc-white) !important;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.25);
}



.cc-header {
    display: flex;
    align-items: center;
    gap: 14px;

    padding: 18px 22px;

    background: var(--cc-white);

    border: 1px solid var(--cc-blue-pale);
    border-radius: 16px;

    box-shadow: 0 4px 18px rgba(11, 61, 102, 0.08);

    margin-bottom: 22px;
}

.cc-header .cc-icon {
    font-size: 34px;

    background: var(--cc-blue-pale);

    width: 56px;
    height: 56px;

    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    flex-shrink: 0;
}

.cc-header h1 {
    color: var(--cc-navy) !important;

    font-size: 22px;

    margin: 0;
}

.cc-header p {
    color: var(--cc-gray) !important;

    margin: 2px 0 0 0;

    font-size: 14px;
}




.cc-badge {
    display: inline-block;

    padding: 4px 12px;

    border-radius: 999px;

    font-size: 12px;

    font-weight: 600;

    margin-top: 6px;
}

.cc-badge-ok {
    background: #e4f6ec;

    color: #1c7a4d !important;

    border: 1px solid #bfe9d2;
}

.cc-badge-err {
    background: #fdeaea;

    color: #b3261e !important;

    border: 1px solid #f6c6c4;
}


  

/*
 
   كل النصوص عاملينها على اللون الغامق
*/

[data-testid="stChatMessage"] {
    border-radius: 16px;

    padding: 8px 10px;

    margin-bottom: 8px;

    color: var(--cc-text) !important;
}

[data-testid="stChatMessageContent"] {
    color: var(--cc-text) !important;

    font-size: 15.5px;

    line-height: 1.9;
}



[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] span,
[data-testid="stChatMessageContent"] div,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] strong,
[data-testid="stChatMessageContent"] em,
[data-testid="stChatMessageContent"] h1,
[data-testid="stChatMessageContent"] h2,
[data-testid="stChatMessageContent"] h3,
[data-testid="stChatMessageContent"] h4,
[data-testid="stChatMessageContent"] h5,
[data-testid="stChatMessageContent"] h6,
[data-testid="stChatMessageContent"] blockquote,
[data-testid="stChatMessageContent"] td,
[data-testid="stChatMessageContent"] th {
    color: var(--cc-text) !important;
}



[data-testid="stChatMessageContent"]
[data-testid="stMarkdownContainer"] {
    color: var(--cc-text) !important;
}

[data-testid="stChatMessageContent"]
[data-testid="stMarkdownContainer"] * {
    color: var(--cc-text) !important;
}



div[data-testid="stChatMessage"]:has(
    div[data-testid="stChatMessageAvatarUser"]
) {
    background: var(--cc-blue-pale);
}



div[data-testid="stChatMessage"]:has(
    div[data-testid="stChatMessageAvatarAssistant"]
) {
    background: var(--cc-white);

    border: 1px solid var(--cc-blue-pale);
}




.rtl {
    direction: rtl;

    text-align: right;

    color: var(--cc-text) !important;

    width: 100%;
}

.rtl * {
    color: var(--cc-text) !important;
}




[data-testid="stChatInput"] {
    background-color: var(--cc-white) !important;
}

[data-testid="stChatInput"] textarea {
    background-color: var(--cc-white) !important;

    color: var(--cc-text) !important;

    -webkit-text-fill-color: var(--cc-text) !important;

    border: 1px solid var(--cc-blue-light) !important;

    border-radius: 14px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--cc-gray) !important;

    opacity: 1 !important;
}




.stButton > button {
    background: var(--cc-blue) !important;

    color: var(--cc-white) !important;

    border-radius: 10px;

    border: none;
}

.stButton > button:hover {
    background: var(--cc-navy) !important;

    color: var(--cc-white) !important;
}



.cc-emergency {
    background: #fdeaea;

    border: 1px solid #f2b8b5;

    color: #8a1f1f !important;

    padding: 12px 16px;

    border-radius: 12px;

    font-weight: 700;

    margin-bottom: 10px;
}




[data-testid="stExpander"] {
    background-color: var(--cc-white) !important;

    border-radius: 12px;

    border: 1px solid var(--cc-blue-pale);
}


/* 
   حماية من Dark Mode
 */

[data-testid="stBottomBlockContainer"] {
    background: var(--cc-blue-paler) !important;
}



[data-testid="stChatMessageContent"] a {
    color: #0b5f94 !important;

    text-decoration: underline;
}



[data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessageContent"] ol {
    color: var(--cc-text) !important;
}


[data-testid="stChatMessageContent"] table {
    color: var(--cc-text) !important;
}

[data-testid="stChatMessageContent"] tr,
[data-testid="stChatMessageContent"] td,
[data-testid="stChatMessageContent"] th {
    color: var(--cc-text) !important;
}



[data-testid="stChatMessageContent"] code {
    color: var(--cc-text) !important;
}



[data-testid="stAlert"] {
    color: var(--cc-text) !important;
}

[data-testid="stAlert"] * {
    color: var(--cc-text) !important;
}

</style>
"""


st.markdown(CUSTOM_CSS, unsafe_allow_html=True)



if "messages" not in st.session_state:
    st.session_state.messages = []


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())



if "agent" not in st.session_state and AGENT_AVAILABLE:

    with st.spinner("جاري تجهيز المساعد..."):

        try:
            st.session_state.agent = create_cairo_care_agent()

            st.session_state.agent_error = None

        except Exception as e:

            st.session_state.agent = None

            st.session_state.agent_error = str(e)

elif not AGENT_AVAILABLE:

    st.session_state.agent = None

    st.session_state.agent_error = AGENT_IMPORT_ERROR




with st.sidebar:

    st.markdown("### 🩺 Cairo Care")

    st.markdown(
        "مساعدك الذكي لإيجاد **أقرب مستشفى** أو **أفضل دكتور** "
        "في القاهرة، حسب حالتك ومنطقتك."
    )

    st.markdown("---")

    st.markdown("#### كيف تستخدمه؟")

    st.markdown(
        "- اكتب **الأعراض** اللي حاسس بيها، وهنرشحلك التخصص المناسب.\n"
        "- أو اسأل مباشرة عن **مستشفى** في منطقة معينة.\n"
        "- أو اطلب **دكتور** بتخصص ومنطقة محددين."
    )

    st.markdown("---")

    st.markdown("#### أمثلة سريعة")

    example_questions = [
        "عندي ألم شديد في الصدر",
        "فين مستشفى قلب في المعادي؟",
        "عايز دكتور جلدية في مصر الجديدة",
        "طفلي عنده حرارة عالية",
    ]

    for q in example_questions:

        if st.button(
            q,
            key=f"ex_{q}",
            use_container_width=True,
        ):
            st.session_state.pending_question = q


    st.markdown("---")


    if st.button(
        "🗑️ مسح المحادثة",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()


    st.markdown("---")

    st.caption(
        "⚠️ Cairo Care أداة مساعدة ولا تغني عن استشارة طبية "
        "أو الطوارئ الفعلية."
    )







status_html = (
    '<span class="cc-badge cc-badge-ok">● المساعد متصل</span>'
    if st.session_state.get("agent") is not None
    else '<span class="cc-badge cc-badge-err">● المساعد غير متاح</span>'
)
st.markdown(
    f"""
    <div class="cc-header rtl">
        <div class="cc-icon">🏥</div>
        <div>
            <h1>Cairo Care</h1>
            <p>مساعدك لإيجاد المستشفيات والأطباء المناسبين في القاهرة</p>
            {status_html}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("agent") is None:
    st.error(
        "تعذّر تحميل المساعد (agent.py). تأكدي إن الملف ده شغّال جنب باقي "
        "ملفات المشروع (config.py, vector_store.py, Cairo_Care/...) وإن كل "
        "المكتبات المطلوبة متثبّتة (requirements.txt)."
    )
    with st.expander("📋 عرض تفاصيل الخطأ كاملة"):
        st.code(str(st.session_state.get("agent_error")), language="text")


# لو الـ Agent غير متاح

if st.session_state.get("agent") is None:

    st.error(
        "تعذّر تحميل المساعد (agent.py). "
        "تأكدي إن الملف ده شغّال جنب باقي ملفات المشروع "
        "(config.py, vector_store.py, Cairo_Care/...) "
        "وإن كل المكتبات المطلوبة متثبّتة."
    )

    with st.expander("📋 عرض تفاصيل الخطأ كاملة"):

        st.code(
            str(st.session_state.get("agent_error")),
            language="text",
        )


def safe_html_text(text: str) -> str:
 

    if text is None:
        return ""

    return html.escape(str(text)).replace(
        "\n",
        "<br>",
    )




for msg in st.session_state.messages:

    avatar = (
        "🧑"
        if msg["role"] == "user"
        else "🩺"
    )

    with st.chat_message(
        msg["role"],
        avatar=avatar,
    ):

        content = safe_html_text(
            msg["content"]
        )

        st.markdown(
            f"""
            <div class="rtl">
                {content}
            </div>
            """,
            unsafe_allow_html=True,
        )






def run_agent(question: str) -> str:

    agent = st.session_state.agent

    full_response = ""

    for chunk, _metadata in agent.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": st.session_state.thread_id
            }
        },
        stream_mode="messages",
    ):

        if (
            chunk.content
            and isinstance(chunk.content, str)
        ):

            full_response += chunk.content

    return full_response



def handle_question(question: str):

    

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )


  

    with st.chat_message(
        "user",
        avatar="🧑",
    ):

        safe_question = safe_html_text(question)

        st.markdown(
            f"""
            <div class="rtl">
                {safe_question}
            </div>
            """,
            unsafe_allow_html=True,
        )




    with st.chat_message(
        "assistant",
        avatar="🩺",
    ):

        placeholder = st.empty()

        placeholder.markdown(
            """
            <div class="rtl">
                ... جاري البحث
            </div>
            """,
            unsafe_allow_html=True,
        )


        try:

            answer = run_agent(question)

        except Exception as e:

            answer = (
                f"⚠️ حصل خطأ أثناء التنفيذ: `{e}`"
            )


       

        safe_answer = safe_html_text(answer)

        placeholder.markdown(
            f"""
            <div class="rtl">
                {safe_answer}
            </div>
            """,
            unsafe_allow_html=True,
        )



    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )



if "pending_question" in st.session_state:

    q = st.session_state.pop(
        "pending_question"
    )

    if st.session_state.get("agent") is not None:

        handle_question(q)

    else:

        st.warning(
            "المساعد غير متاح حالياً، "
            "تأكدي من إعداد المشروع أولاً."
        )



user_input = st.chat_input(
    "اكتب سؤالك هنا... مثال: عايز دكتور عظام في الدقي"
)


if user_input:

    if st.session_state.get("agent") is not None:

        handle_question(user_input)

    else:

        st.warning(
            "المساعد غير متاح حالياً، "
            "تأكدي من إعداد المشروع أولاً."
        )
