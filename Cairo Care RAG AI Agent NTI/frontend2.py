
import streamlit as st
import requests
import uuid
import json
import html


# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="Cairo Care",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)


# =========================================================
# API Configuration
# =========================================================

API_URL = "http://localhost:8000/chat/stream"
HEALTH_URL = "http://localhost:8000/health"


# =========================================================
# Custom CSS
# =========================================================

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


/* =========================
   Sidebar
   ========================= */

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


/* =========================
   Header
   ========================= */

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


/* =========================
   Status Badge
   ========================= */

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


/* =========================
   Chat Messages
   ========================= */

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


/* =========================
   RTL
   ========================= */

.rtl {
    direction: rtl;
    text-align: right;
    color: var(--cc-text) !important;
    width: 100%;
}

.rtl * {
    color: var(--cc-text) !important;
}


/* =========================
   Chat Input
   ========================= */

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


/* =========================
   Buttons
   ========================= */

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


/* =========================
   Emergency
   ========================= */

.cc-emergency {
    background: #fdeaea;

    border: 1px solid #f2b8b5;

    color: #8a1f1f !important;

    padding: 12px 16px;

    border-radius: 12px;

    font-weight: 700;

    margin-bottom: 10px;
}


/* =========================
   Expander
   ========================= */

[data-testid="stExpander"] {
    background-color: var(--cc-white) !important;

    border-radius: 12px;

    border: 1px solid var(--cc-blue-pale);
}


/* =========================
   Dark Mode Protection
   ========================= */

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

st.markdown(
    CUSTOM_CSS,
    unsafe_allow_html=True
)


# =========================================================
# Session State
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())


# =========================================================
# Helper Functions
# =========================================================

def safe_html_text(text: str) -> str:

    if text is None:
        return ""

    return html.escape(
        str(text)
    ).replace(
        "\n",
        "<br>"
    )


def check_backend():

    try:

        response = requests.get(
            HEALTH_URL,
            timeout=2
        )

        if response.status_code == 200:

            data = response.json()

            if data.get("success") is True:
                return True

    except requests.RequestException:
        pass

    return False


# =========================================================
# Check FastAPI Status
# =========================================================

backend_online = check_backend()


if backend_online:

    status_html = (
        '<span class="cc-badge cc-badge-ok">'
        '● المساعد متصل'
        '</span>'
    )

else:

    status_html = (
        '<span class="cc-badge cc-badge-err">'
        '● المساعد غير متصل'
        '</span>'
    )


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown("👨‍⚕️🩺 Cairo Care")

    st.markdown(
        "مساعدك الذكي لإيجاد **أقرب مستشفى** أو "
        "**أفضل دكتور** في القاهرة، حسب حالتك ومنطقتك."
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
            st.rerun()

    st.markdown("---")

    if st.button(
        "🗑️ مسح المحادثة",
        use_container_width=True,
    ):

        st.session_state.messages = []

        st.session_state.thread_id = str(
            uuid.uuid4()
        )

        st.rerun()

    st.markdown("---")

    st.caption(
        "⚠️ Cairo Care أداة مساعدة ولا تغني عن "
        "استشارة طبية أو الطوارئ الفعلية."
    )


# =========================================================
# Header
# =========================================================

st.markdown(
    f"""
    <div class="cc-header rtl">

        <div class="cc-icon">
            🏥
        </div>

        <div>

            <h1>
                Cairo Care
            </h1>

            <p>
                مساعدك لإيجاد المستشفيات والأطباء المناسبين في القاهرة
            </p>

            {status_html}

        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Display Previous Messages
# =========================================================

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


# =========================================================
# Streaming Function
# =========================================================

def stream_response(question: str, placeholder):

    full_response = ""

    payload = {
        "message": question,
        "thread_id": st.session_state.thread_id,
    }

    try:

        with requests.post(
            API_URL,
            json=payload,
            stream=True,
            timeout=(10, 300),
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines(
                decode_unicode=True
            ):

                if not line:
                    continue

                if not line.startswith("data: "):
                    continue

                json_str = line[6:]

                if json_str == "[DONE]":
                    break

                try:

                    data = json.loads(
                        json_str
                    )

                    if data.get("error"):

                        return (
                            f"⚠️ حدث خطأ: "
                            f"{data['error']}"
                        )

                    content = data.get(
                        "content",
                        ""
                    )

                    if content:

                        full_response += content

                        safe_response = safe_html_text(
                            full_response
                        )

                        placeholder.markdown(
                            f"""
                            <div class="rtl">
                                {safe_response}▌
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                except json.JSONDecodeError:

                    continue

    except requests.exceptions.ConnectionError:

        return (
            "⚠️ تعذر الاتصال بالـ Backend. "
            "تأكدي أن FastAPI يعمل على "
            "http://localhost:8000"
        )

    except requests.exceptions.Timeout:

        return (
            "⚠️ انتهت مهلة الاتصال بالسيرفر."
        )

    except requests.exceptions.HTTPError as e:

        return (
            f"⚠️ حدث خطأ من الـ Backend: {e}"
        )

    except Exception as e:

        return (
            f"⚠️ حدث خطأ أثناء الاتصال: {e}"
        )

    return full_response


# =========================================================
# Handle Question
# =========================================================

def handle_question(question: str):

    # Save user message

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Display user message

    with st.chat_message(
        "user",
        avatar="🧑",
    ):

        safe_question = safe_html_text(
            question
        )

        st.markdown(
            f"""
            <div class="rtl">
                {safe_question}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Assistant response

    with st.chat_message(
        "assistant",
        avatar="🩺",
    ):

        placeholder = st.empty()

        placeholder.markdown(
            """
            <div class="rtl">
                ⏳ جاري البحث...
            </div>
            """,
            unsafe_allow_html=True,
        )

        answer = stream_response(
            question,
            placeholder
        )

        # Final response without cursor

        safe_answer = safe_html_text(
            answer
        )

        placeholder.markdown(
            f"""
            <div class="rtl">
                {safe_answer}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Save assistant message

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


# =========================================================
# Pending Question From Sidebar
# =========================================================

if "pending_question" in st.session_state:

    question = st.session_state.pop(
        "pending_question"
    )

    handle_question(
        question
    )


# =========================================================
# Chat Input
# =========================================================

user_input = st.chat_input(
    "اكتب سؤالك هنا..."
)


if user_input:

    handle_question(
        user_input
    )

