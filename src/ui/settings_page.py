"""
ТУТ НИЧЕГО НЕ РЕАЛИЗОВАНО В ДЕЙСТВИЙ
"""
import streamlit as st
import datetime

def show_settings():

    # Get user info
    user_info = st.session_state.user_info
    user_id = user_info['id']
    role = user_info['role']
    
    st.markdown("## ⚙️ Settings")
    st.markdown("Customize your Time Tracker experience")
    
    st.markdown("""
    <style>
    
    .settings-header {
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 1rem;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="settings-container">', unsafe_allow_html=True)
        st.markdown('<div class="settings-header">Profile Settings</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", value=user_info.get('first_name', ''))
            email = st.text_input("Email", value=user_info.get('email', ''), disabled=True)
        
        with col2:
            last_name = st.text_input("Last Name", value=user_info.get('last_name', ''))
            username = st.text_input("Username", value=user_info.get('username', ''), disabled=True)
        
        if st.button("Update Profile", use_container_width=True):
            st.success("Not implemented yet!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="settings-container">', unsafe_allow_html=True)
        st.markdown('<div class="settings-header">Change Password</div>', unsafe_allow_html=True)
        
        current_password = st.text_input("Current Password", type="password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_password = st.text_input("New Password", type="password")
        
        with col2:
            confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.button("Change Password", use_container_width=True):
            if not current_password:
                st.error("Please enter your current password")
            elif not new_password:
                st.error("Please enter a new password")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            else:
                st.success("Not implemented yet!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    

    with st.container():
        st.markdown('<div class="settings-container">', unsafe_allow_html=True)
        st.markdown('<div class="settings-header">Notifications</div>', unsafe_allow_html=True)
        
        st.checkbox("Email notifications for task assignments", value=True)
        st.checkbox("Email notifications for approaching deadlines", value=True)
        st.checkbox("In-app notifications for new messages", value=True)
        st.checkbox("Daily summary email", value=False)
        
        if st.button("Save Notification Settings", use_container_width=True):
            st.success("Notification settings saved!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="settings-container">', unsafe_allow_html=True)
        st.markdown('<div class="settings-header">Calendar Integration</div>', unsafe_allow_html=True)
        
        st.checkbox("Sync tasks with calendar", value=True)
        
        calendar_service = st.selectbox(
            "Calendar Service",
            ["Google Calendar", "Microsoft Outlook", "Apple Calendar", "None"],
            index=0
        )
        
        if calendar_service != "None":
            st.text_input("Calendar ID/Email", value="user@example.com")
            
            if st.button("Connect Calendar", use_container_width=True):
                st.success(f"Connected to {calendar_service}!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="settings-container">', unsafe_allow_html=True)
        st.markdown('<div class="settings-header">Data Export</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export All Time Entries", use_container_width=True):
                st.success("Time entries export initiated. You will receive a download link shortly.")
        
        with col2:
            if st.button("Export All Tasks", use_container_width=True):
                st.success("Tasks export initiated. You will receive a download link shortly.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if role != 'admin':
        with st.container():
            st.markdown('<div class="settings-container">', unsafe_allow_html=True)
            st.markdown('<div class="settings-header">Account</div>', unsafe_allow_html=True)
            
            st.warning("Deleting your account will permanently remove all your data. This action cannot be undone.")
            
            delete_confirmation = st.text_input("Type 'DELETE' to confirm account deletion", "")
            
            if st.button("Delete Account", use_container_width=True):
                if delete_confirmation == "DELETE":
                    st.error("Not implemented yet")
                else:
                    st.error("Not implemented yet,but write 'DELETE'")
            
            st.markdown('</div>', unsafe_allow_html=True)
