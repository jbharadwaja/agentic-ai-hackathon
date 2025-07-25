# 🌐 Standard Library Imports
import os
import json
import io
import datetime

# 🧪 Load environment variables
from dotenv import load_dotenv

# 📦 Third-Party Libraries
import streamlit as st
import google.generativeai as genai
import PyPDF2

# Constants
MEMORY_FILE = "chat_memory.json"

# ------------------ SESSION INIT ------------------
if "selected_role" not in st.session_state:
    st.session_state.selected_role = "General"

if "chat_history" not in st.session_state:
    try:
        with open("chat_history.json", "r") as f:
            st.session_state.chat_history = json.load(f)
    except FileNotFoundError:
        st.session_state.chat_history = []

if "active_chat_index" not in st.session_state:
    st.session_state.active_chat_index = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# 🚀 Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-002")

# 🖥️ Streamlit App Config
st.set_page_config(page_title="Agentic AI Chat", page_icon="🤖")
st.title("🤖 Agentic AI Assistant")

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("🛠️ Settings")

    role = st.selectbox(
        "Choose Role:",
        ["General", "Developer", "Marketer", "Student", "Productivity Coach", "Creative Writer"]
    )
    st.session_state.selected_role = role

    st.markdown("### 📁 Previous Conversations")
    for i, chat in enumerate(st.session_state.chat_history):
        title = chat.get("title", f"Chat {i+1}")
        if st.button(title, key=f"chat_{i}"):
            st.session_state.active_chat_index = i
            st.session_state.messages = chat["messages"]
            st.session_state.selected_role = chat.get("role", "General")
            st.rerun()

# ------------------ ROLE PROMPTS ------------------
role_prompts = {
    "General": "You are a helpful and friendly assistant.",
    "Developer": "You are a technical assistant for developers. Answer with clear explanations and code examples when helpful.",
    "Marketer": "You are a digital marketing assistant. Provide strategies, copy ideas, and funnel suggestions.",
    "Student": "You are a study buddy. Help with explaining topics simply and giving examples.",
    "Productivity Coach": "You are a motivational productivity coach. Help users stay focused, plan, and stay motivated.",
    "Creative Writer": "You are a writing assistant. Help with storytelling, prompts, and creative writing tips."
}
system_prompt = role_prompts.get(role, role_prompts["General"])

st.caption(f"💼 Current Role: *{role}*")
with st.expander("🔧 System Prompt", expanded=False):
    st.code(system_prompt, language="markdown")

# ------------------ DISPLAY CHAT HISTORY ------------------
def format_message(role, content):
    if role == "user":
        return f"""
        <div style='background-color:#f0f2f6; padding:12px; border-radius:10px; margin-bottom:8px;'>
            <b>🧑 You:</b><br>{content}
        </div>
        """
    else:
        return f"""
        <div style='background-color:#e6f4ea; padding:12px; border-radius:10px; margin-bottom:8px;'>
            <b>🤖 AI:</b><br>{content}
        </div>
        """

if st.session_state.active_chat_index is not None:
    st.session_state.messages = st.session_state.chat_history[st.session_state.active_chat_index]["messages"]
else:
    st.session_state.messages = []

for msg in st.session_state.messages:
    html = format_message(msg["role"], msg["content"])
    st.markdown(html, unsafe_allow_html=True)

# ------------------ FILE UPLOAD ------------------
file_text = ""
with st.expander("📄 Upload Reference Document"):
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                file_text += page.extract_text()
        elif uploaded_file.type == "text/plain":
            stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
            file_text = stringio.read()
        file_text = file_text[:3000]
        st.success("✅ File uploaded and text extracted!")

# ------------------ CHAT INPUT ------------------
prompt = st.chat_input("Ask me anything!")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    conversation = system_prompt + "\n\n"
    for msg in st.session_state.messages:
        role_label = "User" if msg["role"] == "user" else "AI"
        conversation += f"{role_label}: {msg['content']}\n"

    with st.chat_message("ai"):
        with st.spinner("🤖 Generating a thoughtful response..."):
            try:
                if file_text:
                    conversation = (
                        system_prompt +
                        "\n\nThe user also uploaded a file with the following content:\n\n" +
                        file_text + "\n\n" + conversation
                    )
                response = model.generate_content(conversation, stream=True)
                full_response = ""
                placeholder = st.empty()
                buffer = ""
                for chunk in response:
                    if chunk.text:
                        buffer += chunk.text
                        if buffer.endswith(" ") or buffer.endswith("\n"):
                            full_response += buffer
                            placeholder.markdown(full_response)
                            buffer = ""
                if buffer:
                    full_response += buffer
                    placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "ai", "content": full_response})
            except Exception as e:
                st.error(f"⚠️ Error generating response: {e}")

    # Update active chat history with new messages
    if st.session_state.active_chat_index is not None:
        st.session_state.chat_history[st.session_state.active_chat_index]["messages"] = st.session_state.messages
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.session_state.chat_history[st.session_state.active_chat_index]["title"] = msg["content"][:30] + "..."
                break
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.chat_history, f)

# ------------------ DOWNLOAD LOG ------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🆕 New Chat"):
        new_chat = {
            "title": "Untitled Chat",
            "role": st.session_state.get("selected_role", "General"),
            "messages": []
        }
        st.session_state.chat_history.append(new_chat)
        st.session_state.active_chat_index = len(st.session_state.chat_history) - 1
        with open("chat_history.json", "w") as f:
            json.dump(st.session_state.chat_history, f)
        st.rerun()

with col2:
    if st.button("🧽 Clear Memory"):
        st.session_state.messages = []
        with open(MEMORY_FILE, "w") as f:
            json.dump([], f)
        st.rerun()

with col3:
    if st.session_state.get("messages"):
        chat_log = json.dumps(st.session_state["messages"], indent=2)
        st.download_button(
            label="💾 Download Chat Log",
            data=chat_log,
            file_name="chat_log.json",
            mime="application/json"
        )

st.markdown("<hr><center>Built for Google x ODSC Hackathon 2025 🚀</center>", unsafe_allow_html=True)
