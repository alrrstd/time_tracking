"""
Внутри проекта реализован только англ. язык
"""
import streamlit as st
import sys
import os

# получаем src путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.auth import AuthManager
from src.ui.login_page import show_login_page
from src.ui.main_app import show_main_app

# Конфиг страницы
st.set_page_config(
    page_title="Time Tracking System",
    page_icon="⏱️",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "mailto:rimalyshev1+help@gmail.com", #SMPT не сделан
        "Report a bug": "mailto:rimalyshev1+bug@gmail.com", #SMPT не сделан
    }
)

# Получаем сессию
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "token" not in st.session_state:
    st.session_state.token = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Login"

# Проверка авторизаций
if st.session_state.token and not st.session_state.authenticated:
    payload = AuthManager.verify_token(st.session_state.token)
    if payload:
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.session_state.token = None
        st.session_state.current_page = "Login"

# Маршрутизация страниц
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()

