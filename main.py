import streamlit as st
from database.db import init_db, get_user_by_nombre
from core.chatbot import TutifrutiBot

# ── Configuración ──
st.set_page_config(
    page_title="TUTIFRUTI",
    page_icon="🤖",
    layout="centered"
)

init_db()

# ── Estados de sesión ──
if "bot"        not in st.session_state:
    st.session_state.bot        = TutifrutiBot()
if "messages"   not in st.session_state:
    st.session_state.messages   = []
if "login_done" not in st.session_state:
    st.session_state.login_done = False
if "login_step" not in st.session_state:
    st.session_state.login_step = "inicio"

# ── Header ──
st.title("🤖 TUTIFRUTI")
st.caption("Asistente académico para gestión del tiempo universitario")
st.divider()

# ══════════════════════════════════════════
# PANTALLA DE LOGIN
# ══════════════════════════════════════════
if not st.session_state.login_done:

    if st.session_state.login_step == "inicio":
        st.subheader("¡Hola! ¿Ya tienes una cuenta?")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Sí, ya tengo cuenta", use_container_width=True):
                st.session_state.login_step = "nombre_existente"
                st.rerun()

        with col2:
            if st.button("🆕 Soy nuevo", use_container_width=True):
                welcome = "¡Hola! Soy TUTIFRUTI 👋\n\nPara empezar, ¿cuál es tu nombre?"
                st.session_state.messages.append({
                    "role": "assistant", "content": welcome
                })
                st.session_state.login_done = True
                st.rerun()

    elif st.session_state.login_step == "nombre_existente":
        st.subheader("¿Cuál es tu nombre?")
        nombre = st.text_input("Escribe tu nombre tal como lo registraste:")

        if st.button("Entrar", use_container_width=True):
            if nombre.strip():
                user = get_user_by_nombre(nombre)
                if user:
                    bienvenida = st.session_state.bot.login(user["user_id"])
                    st.session_state.messages.append({
                        "role": "assistant", "content": bienvenida
                    })
                    st.session_state.login_done = True
                    st.rerun()
                else:
                    st.error(f"No encontré una cuenta con el nombre '{nombre}'.")
                    if st.button("Registrarme como nuevo"):
                        welcome = "¡Hola! Soy TUTIFRUTI 👋\n\nPara empezar, ¿cuál es tu nombre?"
                        st.session_state.messages.append({
                            "role": "assistant", "content": welcome
                        })
                        st.session_state.login_done = True
                        st.rerun()
            else:
                st.warning("Por favor escribe tu nombre.")

# ══════════════════════════════════════════
# PANTALLA DE CHAT
# ══════════════════════════════════════════
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Escribe un mensaje..."):
        st.session_state.messages.append({
            "role": "user", "content": prompt
        })
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                response = st.session_state.bot.process(prompt)
            st.markdown(response)

        st.session_state.messages.append({
            "role": "assistant", "content": response
        })
        st.rerun()