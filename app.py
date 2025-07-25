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

# 🚀 Load environment
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-flash-002")

# 🖥️ Streamlit App Config
st.set_page_config(page_title="Agentic AI Chat", page_icon="🤖")
st.title("🤖 Agentic AI Assistant")

# ------------------ SESSION INIT ------------------
if "selected_role" not in st.session_state:
    st.session_state.selected_role = "General"

if "messages" not in st.session_state:
    try:
        with open(MEMORY_FILE, "r") as f:
            st.session_state.messages = json.load(f)
    except FileNotFoundError:
        st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.header("🛠️ Settings")

    role = st.selectbox(
        "Choose Role:",
        ["General", "Developer", "Marketer", "Student", "Productivity Coach", "Creative Writer"]
    )

    # 📂 Save and Reset
    if st.button("🆕 Start New Conversation"):
        if st.session_state.messages:
            label = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.conversations[label] = st.session_state.messages.copy()
        st.session_state.messages = []

    st.markdown("### 📁 Previous Conversations")
    for label, messages in st.session_state.conversations.items():
        if st.button(label):
            st.session_state.messages = messages
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
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ------------------ CLEAR MEMORY ------------------
if st.button("🧽 Clear Memory"):
    st.session_state.messages = []
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f)
    st.rerun()

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("📄 Upload a PDF or TXT file", type=["pdf", "txt"])
file_text = ""
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

    with open(MEMORY_FILE, "w") as f:
        json.dump(st.session_state.messages, f)

    conversation = system_prompt + "\n\n"
    for msg in st.session_state.messages:
        role_label = "User" if msg["role"] == "user" else "AI"
        conversation += f"{role_label}: {msg['content']}\n"

    with st.chat_message("ai"):
        with st.spinner("Thinking..."):
            try:
                if file_text:
                    prompt_to_send = f"{system_prompt}\n\nThe user also uploaded a file with the following content:\n\n{file_text}\n\nUser: {prompt}"
                else:
                    prompt_to_send = f"{system_prompt}\n\nUser: {prompt}"

                response = model.generate_content(prompt_to_send, stream=True)
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        st.markdown(chunk.text)

                st.session_state.messages.append({"role": "ai", "content": full_response})

            except Exception as e:
                st.error(f"⚠️ Error generating response: {e}")

# ------------------ DOWNLOAD LOG ------------------
if st.session_state["messages"]:
    chat_log = json.dumps(st.session_state["messages"], indent=2)
    st.download_button(
        label="📅 Download Chat Log",
        data=chat_log,
        file_name="chat_log.json",
        mime="application/json"
    )
