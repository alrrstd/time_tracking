
import streamlit as st
import datetime
from typing import Dict, List, Optional
from streamlit_searchbox import st_searchbox
import time

from src.chat import ChatManager

class UserManager:

    @staticmethod
    def get_all_users(exclude_user_id: int = None) -> List[Dict]:
        from ..database import get_db

        db = get_db()

        query = """
        SELECT id, username, first_name, last_name, email, created_at
        FROM users
        """
        params = []

        if exclude_user_id:
            query += " WHERE id != ?"
            params.append(exclude_user_id)

        query += " ORDER BY first_name, last_name"

        try:
            users = db.execute_query(query, params)
            return [dict(user) for user in users]
        except Exception as e:
            st.error(f"Ошибка при получении пользователей: {str(e)}")
            return []

    @staticmethod
    def search_users(query: str, exclude_user_id: int = None) -> List[Dict]:
        from ..database import get_db

        db = get_db()

        if not query:
            return UserManager.get_all_users(exclude_user_id)

        search_query = """
        SELECT id, username, first_name, last_name, email, created_at
        FROM users
        WHERE (
            LOWER(first_name) LIKE LOWER(?) OR
            LOWER(last_name) LIKE LOWER(?) OR
            LOWER(username) LIKE LOWER(?) OR
            LOWER(email) LIKE LOWER(?)
        )
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"]

        if exclude_user_id:
            search_query += " AND id != ?"
            params.append(exclude_user_id)

        search_query += " ORDER BY first_name, last_name"

        try:
            users = db.execute_query(search_query, params)
            return [dict(user) for user in users]
        except Exception as e:
            st.error(f"Ошибка при поиске пользователей: {str(e)}")
            return []

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        from ..database import get_db

        db = get_db()

        try:
            user = db.execute_query(
                "SELECT id, username, first_name, last_name, email FROM users WHERE id = ?",
                (user_id,)
            )
            return dict(user[0]) if user else None
        except Exception as e:
            st.error(f"Ошибка при получении пользователя: {str(e)}")
            return None


def show_chat():


    user_info = st.session_state.user_info
    user_id = user_info["id"]

    if "selected_chat_user" not in st.session_state:
        st.session_state.selected_chat_user = None

    st.markdown("## 💬 Chat")

    st.markdown("""
    <style>
    .stChatMessage {
        margin-bottom: 1rem;
    }
    
    .stChatInput {
        position: sticky;
        bottom: 0;
        background-color: #2C1338;
        padding: 1rem 0;
        border-top: 1px solid #e0e0e0;
    }
    
    
    
    .user-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e0e0e0;
        transition: background-color 0.2s;
    }
    
    .user-card:hover {
        background-color: #f0f0f0;
    }
    
    .conversation-item {
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e9ecef;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .conversation-item:hover {
        background-color: #f8f9fa;
    }
    
    .conversation-item.active {
        background-color: #e3f2fd;
        border-color: #2196f3;
    }
    
    .unread-badge {
        background-color: #ff4444;
        color: white;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 12px;
        text-align: center;
        display: inline-block;
        min-width: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:

        conversations = ChatManager.get_conversations_list(user_id)

        if conversations:
            st.subheader("Active Chats")

            for conv in conversations:
                contact_name = f"{conv["first_name"]} {conv["last_name"]}"

                last_message_time = datetime.datetime.fromisoformat(conv["last_message_time"])
                now = datetime.datetime.now()

                if last_message_time.date() == now.date():
                    time_str = last_message_time.strftime("%H:%M")
                elif (now.date() - last_message_time.date()).days == 1:
                    time_str = "Yesterday"
                else:
                    time_str = last_message_time.strftime("%d.%m")

                message_preview = conv["last_message"][:25] + "..." if len(conv["last_message"]) > 25 else conv["last_message"]

                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        if st.button(
                            f"**{contact_name}**\n{message_preview} • {time_str}",
                            key=f"conv_{conv["user_id"]}",
                            use_container_width=True,
                            help=f"Open chat with {contact_name}"
                        ):
                            st.session_state.selected_chat_user = conv["user_id"]
                            st.rerun()

                    with col2:
                        if conv["unread_count"] > 0:
                            st.markdown(
                                f"<div class=\"unread-badge\">{conv["unread_count"]}</div>",
                                unsafe_allow_html=True
                            )
        else:
            st.info("Not actives chats")

    if st.session_state.selected_chat_user:
        selected_user = UserManager.get_user_by_id(st.session_state.selected_chat_user)

        if not selected_user:
            st.error("User not found")
            return

        col1, col2 = st.columns([4, 1])

        with col1:
            st.subheader(f"💬 {selected_user["first_name"]} {selected_user["last_name"]}")
            st.caption(f"@{selected_user["username"]}")

        with col2:
            if st.button("← Back", use_container_width=True):
                st.session_state.selected_chat_user = None
                st.rerun()

        st.markdown("---")

        messages = ChatManager.get_conversation(user_id, st.session_state.selected_chat_user)
        for message in messages:
            role = "user" if message["is_sent_by_me"] else "assistant"
            with st.chat_message(role):
                st.write(message["message"])
                sent_time = datetime.datetime.fromisoformat(message["sent_at"])
                st.caption(sent_time.strftime("%d.%m.%Y %H:%M"))

        if prompt := st.chat_input("Enter a message..."):
            with st.chat_message("user"):
                st.write(prompt)
                st.caption(datetime.datetime.now().strftime("%d.%m.%Y %H:%M"))

            success, message_text, message_id = ChatManager.send_message(
                sender_id=user_id,
                receiver_id=st.session_state.selected_chat_user,
                message=prompt
            )

            if success:
                st.rerun()
            else:
                st.error(f"Message sending error: {message_text}")

        time.sleep(10) # Задержка по времени для общения в реальном времени - меньше не делать нагружает сервак\пк
        st.rerun()

    else:
        st.markdown("<div class=\"user-search-container\">", unsafe_allow_html=True)
        st.subheader("🔍 Start a new chat")

        def search_users_for_chat(searchterm: str) -> List[str]:
            if not searchterm:
                users = UserManager.get_all_users(exclude_user_id=user_id)
            else:
                users = UserManager.search_users(searchterm, exclude_user_id=user_id)
            return [f"{user["first_name"]} {user["last_name"]} (@{user["username"]}) - {user["id"]}" for user in users]

        selected_user_str = st_searchbox(
            search_users_for_chat,
            key="new_chat_searchbox",
            placeholder="Start typing your name, username or email...",
            label="",
            clear_on_submit=True
        )

        if selected_user_str:
            try:
                selected_user_id = int(selected_user_str.split(" - ")[-1])
                st.session_state.selected_chat_user = selected_user_id
                st.rerun()
            except ValueError:
                st.error("Could not identify the user. Please select from the list.")

        st.markdown("</div>", unsafe_allow_html=True)


