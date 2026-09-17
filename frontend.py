# frontend.py
import streamlit as st
import requests
import uuid
import json

# Page configuration
st.set_page_config(page_title="Cairo Care", page_icon="🏥", layout="centered")

# Custom CSS for the beautiful UI
st.markdown("""
<style>
    /* Import Google Font for Arabic */
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif !important;
    }

    /* Main App Background */
    .stApp {
        background-color: #F7F9FB;
    }
    
    /* Hide the top header bar of Streamlit */
    header {
        visibility: hidden;
    }

    /* Custom Header Card */
    .header-card {
        background: linear-gradient(135deg, #007bff 0%, #00d2ff 100%);
        border-radius: 20px;
        padding: 40px 20px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
        margin-top: -30px;
        box-shadow: 0 10px 20px rgba(0, 123, 255, 0.15);
    }
    .header-icon {
        font-size: 3.5rem;
        margin-bottom: 10px;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.5px;
    }
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.95;
        margin-top: 10px;
        font-weight: 400;
    }

    /* Style Suggestion Buttons */
    div[data-testid="stButton"] > button {
        background-color: white;
        color: #4A4A4A;
        border: 1px solid #EAEAEA;
        border-radius: 12px;
        padding: 15px 10px;
        font-size: 1rem;
        font-weight: 600;
        direction: rtl;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stButton"] > button p {
        font-size: 1rem;
    }
    div[data-testid="stButton"] > button:hover {
        border-color: #007bff;
        color: #007bff;
        box-shadow: 0 4px 10px rgba(0, 123, 255, 0.1);
        transform: translateY(-2px);
    }
    div[data-testid="stButton"] > button:active {
        color: white;
        background-color: #007bff;
    }

    /* Chat Messages Styling */
    [data-testid="stChatMessage"] {
        background-color: white;
        border-radius: 15px;
        padding: 15px 20px;
        margin-bottom: 15px;
        border: 1px solid #F0F0F0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02);
        direction: rtl; /* Puts avatar on the right */
    }
    
    /* Fix Markdown Content inside Chat (Lists, Text Alignment) */
    [data-testid="stMarkdownContainer"] {
        direction: rtl;
        text-align: right;
    }
    
    [data-testid="stMarkdownContainer"] ul, 
    [data-testid="stMarkdownContainer"] ol {
        direction: rtl;
        text-align: right;
        padding-right: 1.5rem; /* Indent bullets from the right */
        padding-left: 0;
    }
    
    /* Make the avatar background invisible/customized */
    [data-testid="stChatMessage"] .st-emotion-cache-1v0mbdj {
        background-color: transparent;
    }
    
    /* Chat Input Styling */
    [data-testid="stChatInput"] {
        direction: rtl;
    }
    [data-testid="stChatInput"] textarea {
        text-align: right;
        direction: rtl;
        font-family: 'Cairo', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Custom Header HTML
st.markdown("""
<div class="header-card">
    <div class="header-icon">🏥</div>
    <h1 class="header-title">Cairo Care</h1>
    <p class="header-subtitle">مساعدك الذكي للمستشفيات والأطباء في القاهرة</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    # Adding the welcome message as requested in the screenshot
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "أهلاً وسهلاً! 👋\n\nأنا \"Cairo Care\"، مساعدك الذكي في القاهرة للعثور على الأطباء والمستشفيات المناسبة.\n\nكيف يمكنني مساعدتك اليوم؟ هل تبحث عن:\n* دكتور متخصص في تخصص معين؟\n* مستشفى قريب منك؟\n* أو أي استشارة طبية أخرى؟\n\nأنا هنا لمساعدتك بكل سرور! 😊"
        }
    ]
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Suggestion Buttons (only show if no user messages exist yet)
if len(st.session_state.messages) <= 1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚨 حاسس بوجع شديد في صدري، انا في شارع التسعين بالتجمع", use_container_width=True):
            st.session_state.suggestion = "حاسس بوجع شديد في صدري ومش قادر اتنفس، انا واقف في شارع التسعين الجنوبي في التجمع الخامس"
        if st.button("🩺 عندي صداع ودوخة، محتاج دكتور في المعادي", use_container_width=True):
            st.session_state.suggestion = "عندي صداع مزمن ودوخة بقالها يومين، محتاج دكتور في المعادي"
    with col2:
        if st.button("📍 إيه المسافة بالسيارة من الدقي لعين شمس التخصصي؟", use_container_width=True):
            st.session_state.suggestion = "إيه هي المسافة والوقت بالسيارة من مكاني في الدقي لحد مستشفى عين شمس التخصصي؟"
        if st.button("👶 انا محتاج دكتور أطفال ضروري", use_container_width=True):
            st.session_state.suggestion = "انا محتاج دكتور أطفال ضروري"

# Display chat history
for msg in st.session_state.messages:
    # Use specific icons based on the screenshot
    avatar = "👤" if msg["role"] == "user" else "🏥"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("اكتب رسالتك هنا... (مثال: فين مستشفى قلب؟)")

# Handle suggestion click
if "suggestion" in st.session_state and st.session_state.suggestion:
    prompt = st.session_state.suggestion
    st.session_state.suggestion = None

if prompt:
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Prepare AI response placeholder
    with st.chat_message("assistant", avatar="🏥"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Call FastAPI backend
        api_url = "http://localhost:8000/chat"
        payload = {
            "message": prompt,
            "thread_id": st.session_state.thread_id
        }
        
        try:
            # Stream the response token-by-token (with connection & read timeouts)
            with requests.post(api_url, json=payload, stream=True, timeout=(5, 60)) as r:
                r.raise_for_status()
                
                # Check if the response is actually Server-Sent Events (SSE) or just plain JSON
                content_type = r.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    # Non-streaming JSON response (if running api.py instead of Backend.py)
                    data = r.json()
                    if "error" in data:
                        full_response = f"⚠️ حدث خطأ: {data['error']}"
                    elif "response" in data:
                        full_response = data["response"]
                    else:
                        full_response = str(data)
                    message_placeholder.markdown(full_response)
                else:
                    # Streaming SSE response
                    for line in r.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                json_str = decoded_line[6:]
                                if json_str == "[DONE]":
                                    break
                                
                                try:
                                    data = json.loads(json_str)
                                    if "error" in data and data["error"]:
                                        full_response = f"⚠️ حدث خطأ: {data['error']}"
                                        break
                                    
                                    # Support both Backend.py ('token') and api.py ('content') formats
                                    token = data.get("token", data.get("content", ""))
                                    full_response += token
                                    
                                    # Display with a blinking cursor effect
                                    message_placeholder.markdown(full_response + "▌")
                                except json.JSONDecodeError:
                                    pass
                    
                    # Final display without the cursor
                    if not full_response:
                        full_response = "⚠️ لم يتم استلام أي رد من السيرفر. (الرد فارغ)"
                    message_placeholder.markdown(full_response)
        except requests.exceptions.Timeout:
            full_response = "⚠️ السيرفر لا يستجيب (انتهى وقت الاتصال). تأكد من تشغيل السيرفر وعدم وجود مشكلة في Ollama."
            message_placeholder.error(full_response)
        except Exception as e:
            full_response = f"⚠️ خطأ في الاتصال بالسيرفر: {e}"
            message_placeholder.error(full_response)
            
    # Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Force a rerun to clear the suggestion buttons if we just sent a suggestion
    st.rerun()