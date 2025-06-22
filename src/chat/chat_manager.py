import datetime
from typing import Dict, List, Optional, Tuple

from ..database import get_db


class ChatManager:
    @staticmethod
    def send_message(sender_id: int, receiver_id: int, message: str) -> Tuple[bool, str, Optional[int]]:

        db = get_db()
        
        if not message or not message.strip():
            return False, "Message cannot be empty", None
        
        receiver = db.execute_query(
            "SELECT id FROM users WHERE id = ?", 
            (receiver_id,)
        )
        
        if not receiver:
            return False, "Receiver not found", None
        
        if sender_id == receiver_id:
            return False, "Cannot send message to yourself", None
        
        try:
            sent_at = datetime.datetime.now().isoformat()
            message_id = db.execute_insert(
                """
                INSERT INTO chat_messages (sender_id, receiver_id, message, sent_at)
                VALUES (?, ?, ?, ?)
                """,
                (sender_id, receiver_id, message, sent_at)
            )
            
            sender_name = db.execute_query(
                "SELECT username FROM users WHERE id = ?", 
                (sender_id,)
            )[0]['username']
            
            db.execute_insert(
                """
                INSERT INTO notifications (user_id, title, message, type, related_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (receiver_id, "New Message", 
                 f"You have a new message from {sender_name}", 
                 "message", message_id, sent_at)
            )
            
            return True, "Message sent successfully", message_id
        except Exception as e:
            return False, f"Failed to send message: {str(e)}", None
    
    @staticmethod
    def mark_messages_as_read(user_id: int, other_user_id: int) -> Tuple[bool, str]:

        db = get_db()
        
        try:
            read_at = datetime.datetime.now().isoformat()
            db.execute_update(
                """
                UPDATE chat_messages 
                SET read_at = ?
                WHERE sender_id = ? AND receiver_id = ? AND read_at IS NULL
                """,
                (read_at, other_user_id, user_id)
            )
            
            return True, "Messages marked as read"
        except Exception as e:
            return False, f"Failed to mark messages as read: {str(e)}"
    
    @staticmethod
    def get_conversation(user_id: int, other_user_id: int, limit: int = 50) -> List[Dict]:
        db = get_db()
        
        messages = db.execute_query(
            """
            SELECT cm.*, 
                  u_sender.username as sender_username,
                  u_receiver.username as receiver_username
            FROM chat_messages cm
            JOIN users u_sender ON cm.sender_id = u_sender.id
            JOIN users u_receiver ON cm.receiver_id = u_receiver.id
            WHERE (cm.sender_id = ? AND cm.receiver_id = ?) OR (cm.sender_id = ? AND cm.receiver_id = ?)
            ORDER BY cm.sent_at DESC
            LIMIT ?
            """,
            (user_id, other_user_id, other_user_id, user_id, limit)
        )
        
        result = []
        for message in messages:
            message_dict = dict(message)
            message_dict['is_sent_by_me'] = message_dict['sender_id'] == user_id
            result.append(message_dict)
        
        ChatManager.mark_messages_as_read(user_id, other_user_id)
        
        return list(reversed(result))
    
    @staticmethod
    def get_conversations_list(user_id: int) -> List[Dict]:
        db = get_db()
        
        conversations = db.execute_query(
            """
            SELECT 
                u.id as user_id,
                u.username,
                u.first_name,
                u.last_name,
                last_msg.message as last_message,
                last_msg.sent_at as last_message_time,
                last_msg.sender_id as last_message_sender_id,
                (SELECT COUNT(*) FROM chat_messages 
                 WHERE sender_id = u.id AND receiver_id = ? AND read_at IS NULL) as unread_count
            FROM users u
            JOIN (
                SELECT 
                    CASE 
                        WHEN sender_id = ? THEN receiver_id 
                        ELSE sender_id 
                    END as other_user_id,
                    message,
                    sent_at,
                    sender_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY 
                            CASE 
                                WHEN sender_id = ? THEN receiver_id 
                                ELSE sender_id 
                            END
                        ORDER BY sent_at DESC
                    ) as rn
                FROM chat_messages
                WHERE sender_id = ? OR receiver_id = ?
            ) last_msg ON u.id = last_msg.other_user_id
            WHERE last_msg.rn = 1 AND u.id != ?
            ORDER BY last_msg.sent_at DESC
            """,
            (user_id, user_id, user_id, user_id, user_id, user_id)
        )
        
        result = []
        for conv in conversations:
            conv_dict = dict(conv)
            conv_dict['is_last_message_from_me'] = conv_dict['last_message_sender_id'] == user_id
            result.append(conv_dict)
        
        return result
    
    @staticmethod
    def get_unread_messages_count(user_id: int) -> int:
        db = get_db()
        
        result = db.execute_query(
            """
            SELECT COUNT(*) as count
            FROM chat_messages
            WHERE receiver_id = ? AND read_at IS NULL
            """,
            (user_id,)
        )
        
        return dict(result[0])['count']
