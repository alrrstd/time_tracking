import streamlit as st
from streamlit_option_menu import option_menu
import datetime

from src.auth import AuthManager
from src.ui.dashboard_page import show_dashboard
from src.ui.time_tracking_page import show_time_tracking
from src.ui.tasks_page import show_tasks
from src.ui.calendar_page import show_calendar
from src.ui.chat_page import show_chat
from src.ui.reports_page import show_reports
from src.ui.settings_page import show_settings
from src.notifications import NotificationManager

def show_main_app():
    """
    Отоброжение UI Части проекта - Ниже можно установить запреты на страницы юзерам и т.д
    """
    
    # --- Custom CSS ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main header styling */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.2rem 1.8rem;
        background-color: #3D2352;
        border-radius: 16px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        color: white;
    }
    
    .app-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #E57CD8;
        display: flex;
        align-items: center;
        letter-spacing: -0.5px;
    }
    
    .app-title-icon {
        margin-right: 0.8rem;
        font-size: 2.2rem;
    }
    
    /* User info styling */
    .user-info {
        display: flex;
        align-items: center;
        background-color: rgba(255,255,255,0.1);
        padding: 0.6rem 1.2rem;
        border-radius: 50px;
        backdrop-filter: blur(5px);
        transition: all 0.3s ease;
    }
    
    .user-info:hover {
        background-color: rgba(255,255,255,0.15);
        transform: translateY(-2px);
    }
    
    .user-name {
        margin-right: 1rem;
        font-weight: 500;
        color: white;
    }
    
    .notification-badge {
        background-color: #FF5252;
        color: white;
        border-radius: 50%;
        padding: 0.1rem 0.4rem;
        font-size: 0.7rem;
        position: absolute;
        top: -5px;
        right: -5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    
    .notification-icon {
        position: relative;
        margin-right: 1rem;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .notification-icon:hover {
        transform: scale(1.1);
    }
    
    /* Sidebar styling */
    .sidebar-header {
        padding: 1.8rem 1rem;
        text-align: center;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        font-weight: 600;
        font-size: 1.2rem;
        color: #E57CD8;
        margin-bottom: 1rem;
    }
    
    .sidebar-footer {
        position: absolute;
        bottom: 0;
        width: 100%;
        padding: 1.2rem;
        text-align: center;
        font-size: 0.85rem;
        color: rgba(255,255,255,0.6);
        border-top: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #6E49CB 0%, #9B6DFF 100%);
        color: white;
        font-weight: 500;
        border-radius: 50px;
        padding: 0.7rem 1.8rem;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 10px rgba(110,73,203,0.3);
        letter-spacing: 0.5px;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #5D3CB0 0%, #8A5CF0 100%);
        box-shadow: 0 6px 15px rgba(110,73,203,0.4);
        transform: translateY(-3px);
    }
    
    .stButton button:active {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(110,73,203,0.4);
    }
    
    /* Timer button styling */
    .timer-button {
        background: linear-gradient(135deg, #E57CD8 0%, #FF9AD5 100%);
        color: white;
        font-weight: 600;
        border-radius: 50px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 6px 15px rgba(229,124,216,0.3);
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.8rem;
    }
    
    .timer-button:hover {
        background: linear-gradient(135deg, #D66BC7 0%, #F589C4 100%);
        box-shadow: 0 8px 20px rgba(229,124,216,0.4);
        transform: translateY(-3px);
    }
    
    .timer-button:active {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(229,124,216,0.4);
    }
    
    .timer-button-icon {
        font-size: 1.3rem;
    }
    
    /* Card styling */
    .card {
        background-color: #3D2352;
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        margin-bottom: 1.8rem;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 1px solid rgba(255,255,255,0.05);
        color: white;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.15);
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #E57CD8;
        margin-bottom: 1.2rem;
        letter-spacing: -0.3px;
    }
    
    .card-metric {
        font-size: 2.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
    }
    
    .card-subtitle {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.7);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 50px;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    
    .badge-primary {
        background-color: rgba(110,73,203,0.2);
        color: #9B6DFF;
    }
    
    .badge-success {
        background-color: rgba(38,203,124,0.2);
        color: #4AE3A2;
    }
    
    .badge-warning {
        background-color: rgba(255,193,7,0.2);
        color: #FFD54F;
    }
    
    .badge-danger {
        background-color: rgba(255,82,82,0.2);
        color: #FF7A7A;
    }
    
    /* Table styling */
    .dataframe {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        background-color: #3D2352;
    }
    
    .dataframe thead th {
        background-color: #2C1338;
        padding: 1rem 1.2rem;
        text-align: left;
        font-weight: 600;
        color: #E57CD8;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: rgba(255,255,255,0.03);
    }
    
    .dataframe tbody td {
        padding: 1rem 1.2rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        color: rgba(255,255,255,0.9);
    }
    
    .dataframe tbody tr:last-child td {
        border-bottom: none;
    }
    
    /* Input fields */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.8rem 1.2rem;
        transition: all 0.3s ease;
        background-color: rgba(255,255,255,0.05);
        color: white;
        font-size: 1rem;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus {
        border-color: #6E49CB;
        box-shadow: 0 0 0 2px rgba(110,73,203,0.2);
        background-color: rgba(255,255,255,0.08);
    }
    
    /* Select boxes */
    .stSelectbox select {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.8rem 1.2rem;
        background-color: rgba(255,255,255,0.05);
        color: white;
    }
    
    /* Progress bars */
    .progress-container {
        width: 100%;
        height: 8px;
        background-color: rgba(255,255,255,0.1);
        border-radius: 4px;
        margin: 1rem 0;
        overflow: hidden;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    .progress-primary {
        background: linear-gradient(90deg, #6E49CB 0%, #9B6DFF 100%);
    }
    
    .progress-success {
        background: linear-gradient(90deg, #26CB7C 0%, #4AE3A2 100%);
    }
    
    .progress-warning {
        background: linear-gradient(90deg, #FFC107 0%, #FFD54F 100%);
    }
    
    .progress-danger {
        background: linear-gradient(90deg, #FF5252 0%, #FF7A7A 100%);
    }
    
    /* Dark mode toggle */
    .dark-mode-toggle {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #2C1338;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        z-index: 1000;
    }
    
    .dark-mode-toggle:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            flex-direction: column;
            gap: 1rem;
            padding: 1rem;
        }
        
        .card {
            padding: 1.2rem;
        }
        
        .card-metric {
            font-size: 2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Часть верстки - Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            '<div class="app-title"><span class="app-title-icon">⏱️</span> Time Tracking System</div>',
            unsafe_allow_html=True
        )
    with col2:
        # Инфа о юзере
        user_info = st.session_state.user_info
        user_name = f"{user_info['first_name']} {user_info['last_name']}" if user_info else "User"
        
        # Кол-во оповещений
        notification_count = NotificationManager.get_unread_count(user_info['id']) if user_info else 0
        
        # Создаем HTML для отображения информации о пользователе
        user_info_html = f"""
        <div class="user-info">
            <span style = "font-size: 0.9rem;" class="user-name">{user_name}</span>
            <div class="notification-icon">
                <span>🔔</span>
                {f'<span class="notification-badge">{notification_count}</span>' if notification_count > 0 else ''}👤
        </div>
        """

        # Отображаем HTML
        st.markdown(user_info_html, unsafe_allow_html=True)

        # Если уведомлений нет, убираем лишний закрывающий тег
        if notification_count == 0:
            st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sidebar-header">Navigation</div>', unsafe_allow_html=True)

        role = user_info['role'] if user_info else 'employee' #Проверка роли юзера
        
        if role == 'employer':
            menu_options = [
                {"icon": "house", "label": "Dashboard"},
                {"icon": "clock", "label": "Time Tracking"},
                {"icon": "list-task", "label": "Tasks"},
                {"icon": "calendar", "label": "Calendar"},
                {"icon": "chat", "label": "Chat"},
                {"icon": "graph-up", "label": "Reports"},
                {"icon": "gear", "label": "Settings"}
            ]
        else:  # employee
            menu_options = [
                {"icon": "house", "label": "Dashboard"},
                {"icon": "clock", "label": "Time Tracking"},
                {"icon": "list-task", "label": "Tasks"},
                {"icon": "calendar", "label": "Calendar"},
                {"icon": "chat", "label": "Chat"},
                {"icon": "graph-up", "label": "Reports"},
                {"icon": "gear", "label": "Settings"}
            ]
        

        # Инициализируйем текущую страницу, если она не установлена
        if "current_page" not in st.session_state or st.session_state.current_page == "Login":
            st.session_state.current_page = "Dashboard"
        
        # Создаем меню
        selected = option_menu(
            menu_title=None,
            options=[option["label"] for option in menu_options],
            icons=[option["icon"] for option in menu_options],
            default_index=[option["label"] for option in menu_options].index(st.session_state.current_page),
            styles={
                "container": {"padding": "0!important", "background-color": "#2C1338", "border-radius": "12px"},
                "icon": {"color": "#E57CD8", "font-size": "1.2rem"},
                "nav-link": {
                    "font-size": "1rem",
                    "text-align": "left",
                    "margin": "0.2rem 0.5rem",
                    "padding": "0.8rem 1rem",
                    "border-radius": "8px",
                    "--hover-color": "#3D2352",
                    "font-weight": "500",
                    "color": "rgba(255,255,255,0.8)",
                    "transition": "all 0.3s ease",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(90deg, #6E49CB 0%, #9B6DFF 100%)",
                    "color": "white",
                    "font-weight": "600",
                    "box-shadow": "0 4px 10px rgba(110,73,203,0.3)",
                },
            },
        )
        
        # Обновляем текущую страницу
        st.session_state.current_page = selected
        
        # Не рабочее, сделано просто для вида
        st.markdown("""
        <div class="dark-mode-toggle" onclick="toggleDarkMode()">
            🌙
        </div>
        <script>
        function toggleDarkMode() {
            document.body.classList.toggle('dark-mode');
            // You would need to save this preference in localStorage or cookies
        }
        </script>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.button("Logout", on_click=logout)
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown(
            '<div style = " font-size: 0.7rem" class="sidebar-footer"><br>© 2025 Time Tracking System - Alyshev. </div>',
            unsafe_allow_html=True
        )
    

    if st.session_state.current_page == "Dashboard":
        show_dashboard()
    elif st.session_state.current_page == "Time Tracking":
        show_time_tracking()
    elif st.session_state.current_page == "Tasks":
        show_tasks()
    elif st.session_state.current_page == "Calendar":
        show_calendar()
    elif st.session_state.current_page == "Chat":
        show_chat()
    elif st.session_state.current_page == "Reports" and user_info['role'] == 'employer' or 'employee':
        show_reports() #Выдаем доступ ролям можем запретить
    elif st.session_state.current_page == "Settings":
        show_settings()
    else:
        show_dashboard()

def logout():
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.token = None
    st.session_state.current_page = "Login"
    st.rerun()
