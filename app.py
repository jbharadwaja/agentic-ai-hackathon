# 🌐 Standard Library Imports
import os         # For environment variables and file handling
import json       # For saving and loading session memory
import io         # For in-memory file handling (used with file uploads)

# 🧪 Environment Variable Loader
from dotenv import load_dotenv  # For loading .env file with API key

# 📦 Third-Party Libraries
import streamlit as st          # Streamlit for the web app interface
import google.generativeai as genai  # Gemini API for content generation
import PyPDF2                   # PDF processing (used to extract text from uploaded PDFs)


MEMORY_FILE = "chat_memory.json"

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load the model
model = genai.GenerativeModel("models/gemini-1.5-flash-002")

# Streamlit UI setup
st.set_page_config(page_title="Agentic AI Chat", page_icon="🤖")
st.title("🤖 Agentic AI Assistant")


role = st.selectbox(
    "🧠 Choose your assistant role:",
    ["General", "Developer", "Marketer", "Student", "Productivity Coach", "Creative Writer"]
)
st.caption(f"💼 Current Role: *{role}*")

# Role-based system prompt (custom instructions to Gemini)
role_prompts = {
    "General": "You are a helpful and friendly assistant.",
    "Developer": "You are a technical assistant for developers. Answer with clear explanations and code examples when helpful.",
    "Marketer": "You are a digital marketing assistant. Provide strategies, copy ideas, and funnel suggestions.",
    "Student": "You are a study buddy. Help with explaining topics simply and giving examples.",
    "Productivity Coach": "You are a motivational productivity coach. Help users stay focused, plan, and stay motivated.",
    "Creative Writer": "You are a writing assistant. Help with storytelling, prompts, and creative writing tips."
}

system_prompt = role_prompts.get(role, role_prompts["General"])
with st.expander("🔧 System Prompt", expanded=False):
    st.code(system_prompt, language="markdown")

# Initialize chat history
if "messages" not in st.session_state:
    try:
        with open(MEMORY_FILE, "r") as f:
            st.session_state.messages = json.load(f)
    except FileNotFoundError:
        st.session_state.messages = []


# Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
if st.button("🧽 Clear Memory"):
    st.session_state.messages = []
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f)
    st.rerun()

# PDF upload
uploaded_file = st.file_uploader("📄 Upload a PDF or TXT file", type=["pdf", "txt"])

# Variable to hold extracted file content
file_text = ""

# ✅ Extract text from uploaded file
if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            file_text += page.extract_text()
    elif uploaded_file.type == "text/plain":
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        file_text = stringio.read()

    # Optional: Limit file text length to avoid Gemini token limits
    file_text = file_text[:3000]  # 🧠 Keep only first 3000 characters (safe for Gemini Flash)
    st.success("✅ File uploaded and text extracted!")
# ---------------- END FILE UPLOAD SECTION ----------------


# Input box
prompt = st.chat_input("Ask me anything!")

if prompt:
    # Add user's message to the conversation
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Save memory to file
    with open(MEMORY_FILE, "w") as f:
        json.dump(st.session_state.messages, f)

    # Build the full memory as a conversation string
    conversation = system_prompt + "\n\n"
    for msg in st.session_state.messages:
        role_label = "User" if msg["role"] == "user" else "AI"
        conversation += f"{role_label}: {msg['content']}\n"

    # Streamlit UI for AI response
    with st.chat_message("ai"):
        with st.spinner("Thinking..."):
            try:
                # 🧠 Build prompt dynamically based on file upload
                if file_text:
                    prompt_to_send = f"{system_prompt}\n\nThe user also uploaded a file with the following content:\n\n{file_text}\n\nUser: {prompt}"
                else:
                    prompt_to_send = f"{system_prompt}\n\nUser: {prompt}"

                # 🔁 Streaming response
                response = model.generate_content(prompt_to_send, stream=True)
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        st.markdown(chunk.text)
                
                st.session_state.messages.append({"role": "ai", "content": full_response})

            except Exception as e:
                st.error(f"⚠️ Error generating response: {e}")


