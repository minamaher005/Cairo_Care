# frontend.py
import streamlit as st
import requests
import uuid
import json

# Page configuration
st.set_page_config(page_title="Cairo Care", page_icon="🏥", layout="centered")

# Custom CSS for better Arabic/RTL support
st.markdown("""
    <style>
    .stChatMessage {
        direction: rtl;
        text-align: right;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏥 Cairo Care")
st.markdown("مساعدك الذكي للمستشفيات والأطباء في القاهرة")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("اكتب رسالتك هنا... (مثال: فين مستشفى قلب؟)"):
    # Add user message to history and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prepare AI response placeholder
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Call FastAPI backend
        api_url = "http://localhost:8000/chat"
        payload = {
            "message": prompt,
            "thread_id": st.session_state.thread_id
        }
        
        try:
            # Stream the response token-by-token
            with requests.post(api_url, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line[6:]
                            if json_str == "[DONE]":
                                break
                            
                            try:
                                data = json.loads(json_str)
                                if "error" in data:
                                    full_response = f"⚠️ حدث خطأ: {data['error']}"
                                    break
                                
                                full_response += data.get("token", "")
                                # Display with a blinking cursor effect
                                message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                pass
                
                # Final display without the cursor
                message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"⚠️ خطأ في الاتصال بالسيرفر: {e}"
            message_placeholder.error(full_response)
            
    # Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})