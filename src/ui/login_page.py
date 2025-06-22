
import streamlit as st
from src.auth import AuthManager

def show_login_page():

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    body {
        background-color: #2C1338;
        color: white;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        color: #E57CD8;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 10px rgba(229,124,216,0.3);
    }
    
    .subtitle {
        font-size: 1.3rem;
        color: rgba(255,255,255,0.8);
        text-align: center;
        margin-bottom: 3rem;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }
    
    
    
    .form-header {
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 2rem;
        color: #E57CD8;
        text-align: center;
        letter-spacing: -0.3px;
    }
    
    .stButton button {
        width: 100%;
        background: linear-gradient(135deg, #6E49CB 0%, #9B6DFF 100%);
        color: white;
        font-weight: 600;
        padding: 0.9rem 0;
        border-radius: 50px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 6px 15px rgba(110,73,203,0.3);
        margin-top: 1.5rem;
        font-size: 1.1rem;
        letter-spacing: 0.5px;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #5D3CB0 0%, #8A5CF0 100%);
        box-shadow: 0 8px 20px rgba(110,73,203,0.4);
        transform: translateY(-3px);
    }
    
    .stButton button:active {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(110,73,203,0.4);
    }
    
    .toggle-text {
        text-align: center;
        margin-top: 2rem;
        font-size: 1rem;
        color: rgba(255,255,255,0.7);
    }
    
    .toggle-link {
        color: #E57CD8;
        cursor: pointer;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .toggle-link:hover {
        text-decoration: underline;
        color: #FF9AD5;
    }
    
    /* Input field styling */
    .stTextInput input, .stNumberInput input, .stDateInput input {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.9rem 1.2rem;
        transition: all 0.3s ease;
        font-size: 1rem;
        background-color: rgba(255,255,255,0.05);
        color: white;
        margin-bottom: 0.5rem;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus {
        border-color: #6E49CB;
        box-shadow: 0 0 0 2px rgba(110,73,203,0.2);
        background-color: rgba(255,255,255,0.08);
    }
    
    /* Label styling */
    .stTextInput label, .stNumberInput label, .stDateInput label, .stSelectbox label {
        color: rgba(255,255,255,0.9);
        font-weight: 500;
        font-size: 0.95rem;
        margin-bottom: 0.3rem;
    }
    
    /* Checkbox styling */
    .stCheckbox label {
        font-size: 0.95rem;
        color: rgba(255,255,255,0.8);
    }
    
    /* Select box styling */
    .stSelectbox select {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        padding: 0.9rem 1.2rem;
        background-color: rgba(255,255,255,0.05);
        color: white;
        font-size: 1rem;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        margin-top: 3rem;
        color: rgba(255,255,255,0.5);
        font-size: 0.9rem;
    }
    
    /* Decorative elements */
    .auth-decoration {
        position: absolute;
        width: 300px;
        height: 300px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(110,73,203,0.2) 0%, rgba(229,124,216,0.1) 50%, rgba(0,0,0,0) 70%);
        z-index: -1;
        filter: blur(40px);
    }
    
    .auth-decoration-1 {
        top: -100px;
        left: -100px;
    }
    
    .auth-decoration-2 {
        bottom: -100px;
        right: -100px;
    }
    
    /* Error message styling */
    .stAlert {
        background-color: rgba(255,82,82,0.1);
        color: #FF7A7A;
        border: 1px solid rgba(255,82,82,0.2);
        border-radius: 12px;
        padding: 0.8rem 1rem;
    }
    
    /* Success message styling */
    .element-container:has(.stAlert) {
        background-color: rgba(38,203,124,0.1);
        color: #4AE3A2;
        border: 1px solid rgba(38,203,124,0.2);
        border-radius: 12px;
        padding: 0.8rem 1rem;
    }
    </style>
    
    <div class="auth-decoration auth-decoration-1"></div>
    <div class="auth-decoration auth-decoration-2"></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">⏱️ Time Tracking System</div>', unsafe_allow_html=True)
    st.markdown('<div style = "font-size: 1.1rem;" class="subtitle">A time tracking software to bring all your time data at one central place.</div>', unsafe_allow_html=True)

    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    if "reg_first_name" not in st.session_state:
        st.session_state.reg_first_name = ""
    if "reg_last_name" not in st.session_state:
        st.session_state.reg_last_name = ""
    if "reg_username" not in st.session_state:
        st.session_state.reg_username = ""
    if "reg_email" not in st.session_state:
        st.session_state.reg_email = ""
    if "reg_password" not in st.session_state:
        st.session_state.reg_password = ""
    if "reg_confirm" not in st.session_state:
        st.session_state.reg_confirm = ""

    def toggle_form():
        st.session_state.show_register = not st.session_state.show_register
        if not st.session_state.show_register: #Чистка полей
            st.session_state.reg_first_name = ""
            st.session_state.reg_last_name = ""
            st.session_state.reg_username = ""
            st.session_state.reg_email = ""
            st.session_state.reg_password = ""
            st.session_state.reg_confirm = ""

    with st.container():
        None

        if not st.session_state.show_register:
            st.markdown('<div class="form-header">Login to your account</div>', unsafe_allow_html=True)

            username_email = st.text_input("Username or Email", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")

            col1, col2 = st.columns([3, 1])
            with col1:
                remember_me = st.checkbox("Remember me")

            login_button = st.button("Login")

            if login_button:
                if not username_email or not password:
                    st.error("Please enter both username/email and password")
                else:
                    success, message, user_data = AuthManager.login_user(username_email, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user_data
                        st.session_state.token = user_data['token']
                        st.session_state.current_page = "Dashboard"
                        st.rerun()
                    else:
                        st.error(message)

            st.markdown('<div class="toggle-text">Don\'t have an account? <span class="toggle-link" onclick="document.querySelector(\'[data-testid=stSidebar]\').querySelector(\'button[kind=secondary]\').click()">Register now</span></div>', unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                st.button("Sign Up ", key="register_toggle", on_click=toggle_form, type="secondary", help="Switch to registration form",use_container_width=100)

        else:
            st.markdown('<div class="form-header">Create a new account</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="reg_first_name", value=st.session_state.reg_first_name)
            with col2:
                last_name = st.text_input("Last Name", key="reg_last_name", value=st.session_state.reg_last_name)

            username = st.text_input("Username", key="reg_username", value=st.session_state.reg_username)
            email = st.text_input("Email", key="reg_email", value=st.session_state.reg_email)

            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("Password", type="password", key="reg_password", value=st.session_state.reg_password)
            with col2:
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm", value=st.session_state.reg_confirm)

            role = st.selectbox("Role", ["employee", "employer"], key="reg_role")

            terms = st.checkbox("I agree to the Terms and Conditions")

            register_button = st.button("Register")

            if register_button:
                if not all([first_name, last_name, username, email, password, confirm_password]):
                    st.error("Please fill in all fields")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif not terms:
                    st.error("You must agree to the Terms and Conditions")
                else:
                    success, message, user_id = AuthManager.register_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        role=role
                    )

                    if success:
                        st.success(f"Registration successful! You can now log in.")
                        st.session_state.show_register = False
                        if  st.session_state.show_register:
                            st.session_state.reg_first_name = ""
                            st.session_state.reg_last_name = ""
                            st.session_state.reg_username = ""
                            st.session_state.reg_email = ""
                            st.session_state.reg_password = ""
                            st.session_state.reg_confirm = ""
                        st.rerun()
                    else:
                        st.error(message)

            st.markdown('<div class="toggle-text">Already have an account? <span class="toggle-link" onclick="document.querySelector(\'[data-testid=stSidebar]\').querySelector(\'button[kind=secondary]\').click()">Login instead</span></div>', unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col2:
                st.button("Sign In", key="login_toggle", on_click=toggle_form, type="secondary", help="Switch to login form", use_container_width=100)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; color: #777; font-size: 1.2rem;">
        © 2025 Time Tracking System - Alyshev.
    </div>
    """, unsafe_allow_html=True)
