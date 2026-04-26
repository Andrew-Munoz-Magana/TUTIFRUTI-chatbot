import streamlit as st
from database.db import init_db
from core.chatbot import TutifrutiBot

# ── Configuración de la página ──
st.set_page_config(
    page_title="TUTIFRUTI",
    page_icon="🤖",
    layout="centered"
)

# ── Inicializar base de datos ──
init_db()

# ── Inicializar el bot en la sesión ──
if "bot" not in st.session_state:
    st.session_state.bot = TutifrutiBot()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "started" not in st.session_state:
    st.session_state.started = False

# ── Header ──
st.title("🤖 TUTIFRUTI")
st.caption("Asistente académico para gestión del tiempo universitario")
st.divider()

# ── Mensaje de bienvenida (solo la primera vez) ──
if not st.session_state.started:
    welcome = "¡Hola! Soy TUTIFRUTI, tu asistente académico 👋\n\nPara empezar, ¿cuál es tu nombre?"
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome
    })
    st.session_state.started = True

# ── Mostrar historial de mensajes ──
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input del usuario ──
if prompt := st.chat_input("Escribe un mensaje..."):

    # Mostrar mensaje del usuario
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    with st.chat_message("user"):
        st.markdown(prompt)

    # Obtener respuesta del bot
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = st.session_state.bot.process(prompt)
        st.markdown(response)

    # Guardar respuesta en historial
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })