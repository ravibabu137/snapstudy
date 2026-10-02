import smtplib
from email.mime.text import MIMEText

import streamlit as st
from google import genai
from google.genai import types

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.1-flash-lite"
st.set_page_config(page_title="Snap&Study", page_icon="📚")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()



def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"


def send_email(to_address, user_name, summary):
    try:
        body = f"Hi {user_name},\n\nHere's your SnapStudy summary:\n\n{summary}"
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = "Your SnapStudy summary 📚"
        message["From"] = GMAIL_ADDRESS
        message["To"] = to_address
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(message)
        return True, "sent"
    except Exception as error:
        return False, str(error)

    
# Step 1: onboarding
if "onboarded" not in st.session_state:
    st.title("📸Snap&Study📚")
    st.caption("Snap it. Understand it. Email yourself the notes.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        email = st.text_input(
            "Your email",
            placeholder="you@example.com",
            help="This is where SnapStudy will send your summary.",
        )
        submitted = st.form_submit_button("Let's go 🚀")
    if submitted:
        if not name.strip() or "@" not in email:
            st.warning("Please enter your name and a valid email address.")
        else:
            st.session_state.name = name.strip()
            st.session_state.email = email.strip()
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()


# Step 2: chat interface
header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("📚 SnapStudy")

with button_col:
    send_disabled = len(st.session_state.messages) <= 2
    if st.button("📤 Send to Email", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your session..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
        success, info = send_email(st.session_state.email, st.session_state.name, summary)
        if success:
            st.success("Sent! Check your inbox (and spam) 📬")
        else:
            st.error(f"Couldn't send that: {info}")
            
st.caption(f"Logged in as {st.session_state.name} - updates go to {st.session_state.email}")

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)


user_input = st.chat_input(
    "Ask a question, or attach a photo of a problem or notes",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("Explain what this is and help me understand it.")

    with st.spinner("Studying it..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)

