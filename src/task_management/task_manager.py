import datetime
from typing import Dict, List, Optional, Tuple

from ..database.schema import get_db


class TaskManager:


    @staticmethod
    def create_task(title: str, description: Optional[str], status: str, priority: str,
                    created_by: int, assigned_to: Optional[int] = None,
                    deadline: Optional[str] = None, estimated_hours: Optional[float] = None) -> Tuple[
        bool, str, Optional[int]]:
        """
        Создаем новый таск
        Возвращает кортеж (success, message, task_id).
        """
        db = get_db()

        try:
            # Валидация инпутов
            if not title or len(title.strip()) < 3:
                return False, "Task title must be at least 3 characters long", None

            if status not in ["not_started", "in_progress", "paused", "completed", "cancelled"]:
                return False, "Invalid task status", None

            if priority and priority not in ["low", "medium", "high", "urgent"]:
                return False, "Invalid task priority", None

            # Чекаем есть ли юзер назначения
            if assigned_to:
                assigned_user = db.execute_query(
                    "SELECT id FROM users WHERE id = ?",
                    (assigned_to,)
                )

                if not assigned_user:
                    return False, "Assigned user not found", None

            # Вставляем новый таск
            task_id = db.execute_insert(
                """
                INSERT INTO tasks (title, description, status, priority, created_by, assigned_to, 
                                  created_at, deadline, estimated_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, description, status, priority, created_by, assigned_to,
                 datetime.datetime.now().isoformat(), deadline, estimated_hours)
            )

            #  Создаем уведомление для назначенного пользователя, если это применимо
            if assigned_to and assigned_to != created_by:
                db.execute_insert(
                    """
                    INSERT INTO notifications (user_id, title, message, type, related_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (assigned_to, "New Task Assigned",
                     f"You have been assigned a new task: {title}",
                     "task", task_id, datetime.datetime.now().isoformat())
                )

            return True, "Task created successfully", task_id
        except Exception as e:
            return False, f"Task creation failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def update_task(task_id: int, user_id: int, updates: Dict) -> Tuple[bool, str]:
        """
        Обновка текущего таска.
        Возвращаем кортеж (success, message).
        """
        db = get_db()

        try:
            task = db.execute_query(
                "SELECT id, created_by, assigned_to FROM tasks WHERE id = ?",
                (task_id,)
            )

            if not task:
                return False, "Task not found"

            task_data = dict(task[0])

            if user_id != task_data["created_by"] and user_id != task_data["assigned_to"]:
                return False, "You don't have permission to update this task"

            # Валидация апдейтов
            if "status" in updates and updates["status"] not in ["not_started", "in_progress", "paused", "completed",
                                                                 "cancelled"]:
                return False, "Invalid task status"

            if "priority" in updates and updates["priority"] not in ["low", "medium", "high", "urgent"]:
                return False, "Invalid task priority"

            # Создаем запрос на обновку
            update_fields = []
            params = []

            for field, value in updates.items():
                if field in ["title", "description", "status", "priority", "deadline", "estimated_hours"]:
                    update_fields.append(f"{field} = ?")
                    params.append(value)

            if "assigned_to" in updates:
                if updates["assigned_to"]:
                    assigned_user = db.execute_query(
                        "SELECT id FROM users WHERE id = ?",
                        (updates["assigned_to"],)
                    )

                    if not assigned_user:
                        return False, "Assigned user not found"

                    update_fields.append("assigned_to = ?")
                    params.append(updates["assigned_to"])


                    if updates["assigned_to"] != task_data["assigned_to"] and updates["assigned_to"] != user_id:
                        task_title = db.execute_query(
                            "SELECT title FROM tasks WHERE id = ?",
                            (task_id,)
                        )[0]["title"]

                        db.execute_insert(
                            """
                            INSERT INTO notifications (user_id, title, message, type, related_id, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (updates["assigned_to"], "Task Assigned",
                             f"You have been assigned to task: {task_title}",
                             "task", task_id, datetime.datetime.now().isoformat())
                        )

            if "status" in updates and updates["status"] == "completed":
                update_fields.append("completed_at = ?")
                params.append(datetime.datetime.now().isoformat())

            if not update_fields:
                return False, "No valid fields to update"

            # Делаем апдейт
            params.append(task_id)

            db.execute_update(
                f"UPDATE tasks SET {", ".join(update_fields)} WHERE id = ?",
                tuple(params)
            )

            return True, "Task updated successfully"
        except Exception as e:
            return False, f"Task update failed: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def delete_task(task_id: int, user_id: int) -> Tuple[bool, str]:
        """
        Удаляем таск
        Возвращаем кортеж (success, message).
        """
        db = get_db()

        try:
            task = db.execute_query(
                "SELECT id, created_by FROM tasks WHERE id = ?",
                (task_id,)
            )

            if not task:
                return False, "Task not found"

            # Только создатель таска может удалить таск
            if user_id != dict(task[0])["created_by"]:
                return False, "You don't have permission to delete this task"

            time_entries = db.execute_query(
                "SELECT COUNT(*) as count FROM time_entries WHERE task_id = ?",
                (task_id,)
            )

            if dict(time_entries[0])["count"] > 0:
                db.execute_update(
                    "UPDATE tasks SET status = 'cancelled' WHERE id = ?",
                    (task_id,)
                )
                return True, "Task has time entries and was marked as cancelled instead of deleted"
            else:

                db.execute_update(
                    "DELETE FROM tasks WHERE id = ?",
                    (task_id,)
                )
                return True, "Task deleted successfully"
        except Exception as e:
            return False, f"Task deletion failed: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def get_task(task_id: int, user_id: int) -> Optional[Dict]:
        """
        Получаем id таска
        """
        db = get_db()

        try:
            task = db.execute_query(
                """
                SELECT t.*, 
                      u_creator.username as creator_username,
                      u_assignee.username as assignee_username
                FROM tasks t
                JOIN users u_creator ON t.created_by = u_creator.id
                LEFT JOIN users u_assignee ON t.assigned_to = u_assignee.id
                WHERE t.id = ? AND (t.created_by = ? OR t.assigned_to = ?)
                """,
                (task_id, user_id, user_id)
            )

            if not task:
                return None

            return dict(task[0])
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_tasks(user_id: Optional[int] = None, status: Optional[str] = None,
                  priority: Optional[str] = None, role: str = "all", search: Optional[str] = None,
                  limit: Optional[int] = None) -> List[Dict]:
        """Получаем таски"""
        db = get_db()

        try:
            query = """
            SELECT t.*, 
                   u_creator.username AS creator_username,
                   u_assignee.username AS assignee_username
            FROM tasks t
            LEFT JOIN users u_creator ON t.created_by = u_creator.id
            LEFT JOIN users u_assignee ON t.assigned_to = u_assignee.id
            """
            params = []

            if user_id is not None:
                query += " WHERE t.created_by = ? OR t.assigned_to = ?"
                params.extend([user_id, user_id])

            if status:
                query += " AND t.status = ?"
                params.append(status)

            if priority:
                query += " AND t.priority = ?"
                params.append(priority)

            if search:
                query += " AND (t.title LIKE ? OR t.description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)

            tasks = db.execute_query(query, tuple(params))
            return [dict(task) for task in tasks]
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def get_task_statistics(user_id: Optional[int] = None) -> Dict:
        """
        Получаем статистику по таскам для пользователя или всех пользователей, если user_id равен None.
        Возвращает словарь с количеством тасков, степенью их выполнения и предстоящими сроками.
        """
        db = get_db()

        try:
            user_filter = "WHERE created_by = ? OR assigned_to = ?" if user_id is not None else ""
            user_param = (user_id, user_id) if user_id is not None else ()

            # Получаем таски по статусу
            status_counts = db.execute_query(
                f"""
                SELECT status, COUNT(*) as count
                FROM tasks
                {user_filter}
                GROUP BY status
                """,
                user_param
            )

            # Стутусы словарик
            status_counts_dict = {
                "not_started": 0,
                "in_progress": 0,
                "paused": 0,
                "completed": 0,
                "cancelled": 0
            }


            for row in status_counts:
                status_counts_dict[row["status"]] = row["count"]

            # Считаем продуктивность
            total_tasks = sum(status_counts_dict.values())
            completed_tasks = status_counts_dict["completed"]
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Дедлайны
            upcoming_deadlines = db.execute_query(
                f"""
                SELECT title, deadline
                FROM tasks
                {user_filter} {"AND" if user_filter else "WHERE"} deadline IS NOT NULL AND deadline > ?
                ORDER BY deadline ASC
                """,
                user_param + (datetime.datetime.now().isoformat(),)
            )

            # Приотирет
            priority_counts = db.execute_query(
                f"""
                SELECT priority, COUNT(*) as count
                FROM tasks
                {user_filter}
                GROUP BY priority
                """,
                user_param
            )


            priority_counts_dict = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "urgent": 0
            }

            for row in priority_counts:
                priority_counts_dict[row["priority"]] = row["count"]

            return {
                "status_counts": status_counts_dict,
                "completion_rate": completion_rate,
                "upcoming_deadlines": [dict(deadline) for deadline in upcoming_deadlines],
                "priority_counts": priority_counts_dict
            }
        except Exception as e:
            print(f"Error getting task statistics: {e}")
            return {
                "status_counts": {},
                "completion_rate": 0,
                "upcoming_deadlines": [],
                "priority_counts": {}
            }
        finally:
            db.close()

