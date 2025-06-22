
import datetime
from typing import Dict, List, Optional, Tuple

from ..database import get_db


class NotificationManager:

    @staticmethod
    def create_notification(user_id: int, title: str, message: str,
                           notification_type: str, related_id: Optional[int] = None) -> Tuple[bool, str, Optional[int]]:

        db = get_db()

        if not title or not title.strip():
            return False, "Notification title cannot be empty", None

        if not message or not message.strip():
            return False, "Notification message cannot be empty", None

        if notification_type not in ['task', 'deadline', 'message', 'system']:
            return False, "Invalid notification type", None

        try:
            created_at = datetime.datetime.now().isoformat()
            notification_id = db.execute_insert(
                """
                INSERT INTO notifications (user_id, title, message, type, related_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, message, notification_type, related_id, created_at)
            )

            return True, "Notification created successfully", notification_id
        except Exception as e:
            return False, f"Failed to create notification: {str(e)}", None

    @staticmethod
    def mark_as_read(notification_id: int, user_id: int) -> Tuple[bool, str]:

        db = get_db()

        notification = db.execute_query(
            "SELECT id FROM notifications WHERE id = ? AND user_id = ?",
            (notification_id, user_id)
        )

        if not notification:
            return False, "Notification not found or you don't have permission to access it"

        try:
            read_at = datetime.datetime.now().isoformat()
            db.execute_update(
                "UPDATE notifications SET read_at = ? WHERE id = ?",
                (read_at, notification_id)
            )

            return True, "Notification marked as read"
        except Exception as e:
            return False, f"Failed to mark notification as read: {str(e)}"

    @staticmethod
    def mark_all_as_read(user_id: int) -> Tuple[bool, str]:

        db = get_db()

        try:
            read_at = datetime.datetime.now().isoformat()
            db.execute_update(
                "UPDATE notifications SET read_at = ? WHERE user_id = ? AND read_at IS NULL",
                (read_at, user_id)
            )

            return True, "All notifications marked as read"
        except Exception as e:
            return False, f"Failed to mark notifications as read: {str(e)}"

    @staticmethod
    def delete_notification(notification_id: int, user_id: int) -> Tuple[bool, str]:

        db = get_db()

        notification = db.execute_query(
            "SELECT id FROM notifications WHERE id = ? AND user_id = ?",
            (notification_id, user_id)
        )

        if not notification:
            return False, "Notification not found or you don't have permission to delete it"

        try:
            db.execute_update(
                "DELETE FROM notifications WHERE id = ?",
                (notification_id,)
            )

            return True, "Notification deleted successfully"
        except Exception as e:
            return False, f"Failed to delete notification: {str(e)}"

    @staticmethod
    def get_notifications(user_id: int, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        db = get_db()

        query = """
        SELECT *
        FROM notifications
        WHERE user_id = ?
        """

        params = [user_id]

        if unread_only:
            query += " AND read_at IS NULL"

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        notifications = db.execute_query(query, tuple(params))

        result = []
        for notification in notifications:
            result.append(dict(notification))

        return result

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        db = get_db()

        result = db.execute_query(
            """
            SELECT COUNT(*) as count
            FROM notifications
            WHERE user_id = ? AND read_at IS NULL
            """,
            (user_id,)
        )

        return dict(result[0])['count']

    @staticmethod
    def create_deadline_notifications() -> int:

        db = get_db()

        now = datetime.datetime.now()
        tomorrow = (now + datetime.timedelta(days=1)).isoformat()

        tasks = db.execute_query(
            """
            SELECT t.id, t.title, t.deadline, t.assigned_to, u.username
            FROM tasks t
            JOIN users u ON t.assigned_to = u.id
            WHERE t.deadline IS NOT NULL
            AND t.deadline > ?
            AND t.deadline < ?
            AND t.status NOT IN ('completed', 'cancelled')
            AND NOT EXISTS (
                SELECT 1 FROM notifications n
                WHERE n.related_id = t.id
                AND n.type = 'deadline'
                AND n.created_at > ?
            )
            """,
            (now.isoformat(), tomorrow, (now - datetime.timedelta(hours=24)).isoformat())
        )

        notification_count = 0

        for task in tasks:
            task_data = dict(task)
            deadline = datetime.datetime.fromisoformat(task_data['deadline'])
            hours_remaining = (deadline - now).total_seconds() / 3600

            if hours_remaining <= 2:
                title = "⚠️ URGENT: Task Deadline in Less Than 2 Hours"
                message = f"Task '{task_data['title']}' is due in less than 2 hours!"
            elif hours_remaining <= 8:
                title = "⚠️ Task Deadline Today"
                message = f"Task '{task_data['title']}' is due in {int(hours_remaining)} hours!"
            else:
                title = "Upcoming Task Deadline"
                message = f"Task '{task_data['title']}' is due in {int(hours_remaining)} hours!"

            success, _, _ = NotificationManager.create_notification(
                user_id=task_data['assigned_to'],
                title=title,
                message=message,
                notification_type='deadline',
                related_id=task_data['id']
            )

            if success:
                notification_count += 1

        return notification_count
