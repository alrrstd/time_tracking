import datetime
from typing import Dict, List, Optional, Tuple

from ..database import get_db


class TimeTracker:

    @staticmethod
    def start_time_entry(user_id: int, task_id: int, comment: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:

        db = get_db()

        try:
            task = db.execute_query(
                "SELECT id, status FROM tasks WHERE id = ? AND (assigned_to = ? OR created_by = ?)",
                (task_id, user_id, user_id)
            )

            if not task:
                return False, "Task not found or not assigned to you", None

            task_status = dict(task[0])["status"]
            if task_status in ["completed", "cancelled"]:
                return False, f"Cannot track time for a {task_status} task", None

            active_entries = db.execute_query(
                "SELECT id, task_id FROM time_entries WHERE user_id = ? AND end_time IS NULL",
                (user_id,)
            )

            if active_entries:
                active_entry = dict(active_entries[0])
                return False, f"You already have an active time entry for task #{active_entry['task_id']}", None

            if task_status != "in_progress":
                db.execute_update(
                    "UPDATE tasks SET status = 'in_progress' WHERE id = ?",
                    (task_id,)
                )

            start_time = datetime.datetime.now().isoformat()
            time_entry_id = db.execute_insert(
                """
                INSERT INTO time_entries (user_id, task_id, start_time, comment, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, task_id, start_time, comment, start_time)
            )

            return True, "Time tracking started", time_entry_id
        except Exception as e:
            return False, f"Failed to start time tracking: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def pause_time_entry(user_id: int) -> Tuple[bool, str, Optional[Dict]]:

        db = get_db()

        try:
            active_entries = db.execute_query(
                """
                SELECT te.id, te.task_id, te.start_time, t.title 
                FROM time_entries te
                JOIN tasks t ON te.task_id = t.id
                WHERE te.user_id = ? AND te.end_time IS NULL
                """,
                (user_id,)
            )

            if not active_entries:
                return False, "No active time entry found", None

            active_entry = dict(active_entries[0])

            start_time = datetime.datetime.fromisoformat(active_entry["start_time"])
            end_time = datetime.datetime.now()
            duration_seconds = int((end_time - start_time).total_seconds())

            end_time_str = end_time.isoformat()
            db.execute_update(
                """
                UPDATE time_entries 
                SET end_time = ?, duration_seconds = ?
                WHERE id = ?
                """,
                (end_time_str, duration_seconds, active_entry["id"])
            )

            db.execute_update(
                "UPDATE tasks SET status = 'paused' WHERE id = ?",
                (active_entry["task_id"],)
            )

            time_entry_data = {
                "id": active_entry["id"],
                "task_id": active_entry["task_id"],
                "task_title": active_entry["title"],
                "start_time": active_entry["start_time"],
                "end_time": end_time_str,
                "duration_seconds": duration_seconds,
                "duration_formatted": TimeTracker.format_duration(duration_seconds)
            }

            return True, "Time tracking paused", time_entry_data
        except Exception as e:
            return False, f"Failed to pause time tracking: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def stop_time_entry(user_id: int, comment: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:

        db = get_db()

        try:
            active_entries = db.execute_query(
                """
                SELECT te.id, te.task_id, te.start_time, te.comment, t.title 
                FROM time_entries te
                JOIN tasks t ON te.task_id = t.id
                WHERE te.user_id = ? AND te.end_time IS NULL
                """,
                (user_id,)
            )

            if not active_entries:
                return False, "No active time entry found", None

            active_entry = dict(active_entries[0])

            start_time = datetime.datetime.fromisoformat(active_entry["start_time"])
            end_time = datetime.datetime.now()
            duration_seconds = int((end_time - start_time).total_seconds())

            entry_comment = comment if comment else active_entry["comment"]

            end_time_str = end_time.isoformat()
            db.execute_update(
                """
                UPDATE time_entries 
                SET end_time = ?, duration_seconds = ?, comment = ?
                WHERE id = ?
                """,
                (end_time_str, duration_seconds, entry_comment, active_entry["id"])
            )

            time_entry_data = {
                "id": active_entry["id"],
                "task_id": active_entry["task_id"],
                "task_title": active_entry["title"],
                "start_time": active_entry["start_time"],
                "end_time": end_time_str,
                "duration_seconds": duration_seconds,
                "duration_formatted": TimeTracker.format_duration(duration_seconds),
                "comment": entry_comment
            }

            return True, "Time tracking stopped", time_entry_data
        except Exception as e:
            return False, f"Failed to stop time tracking: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def get_active_time_entry(user_id: int) -> Optional[Dict]:
        db = get_db()

        try:
            active_entries = db.execute_query(
                """
                SELECT te.id, te.task_id, te.start_time, te.comment, t.title 
                FROM time_entries te
                JOIN tasks t ON te.task_id = t.id
                WHERE te.user_id = ? AND te.end_time IS NULL
                """,
                (user_id,)
            )

            if not active_entries:
                return None

            active_entry = dict(active_entries[0])

            start_time = datetime.datetime.fromisoformat(active_entry["start_time"])
            current_time = datetime.datetime.now()
            duration_seconds = int((current_time - start_time).total_seconds())

            return {
                "id": active_entry["id"],
                "task_id": active_entry["task_id"],
                "task_title": active_entry["title"],
                "start_time": active_entry["start_time"],
                "duration_seconds": duration_seconds,
                "duration_formatted": TimeTracker.format_duration(duration_seconds),
                "comment": active_entry["comment"]
            }
        except Exception as e:
            print(f"Error getting active time entry: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def get_time_entries(user_id: int, task_id: Optional[int] = None,
                         start_date: Optional[str] = None, end_date: Optional[str] = None,
                         limit: int = 100) -> List[Dict]:
        db = get_db()

        try:
            query = """
            SELECT te.id, te.task_id, te.start_time, te.end_time, te.duration_seconds, te.comment,
                   t.title as task_title
            FROM time_entries te
            JOIN tasks t ON te.task_id = t.id
            WHERE te.user_id = ?
            """
            params = [user_id]

            if task_id:
                query += " AND te.task_id = ?"
                params.append(task_id)

            if start_date:
                query += " AND te.start_time >= ?"
                params.append(start_date)

            if end_date:
                query += " AND te.start_time <= ?"
                params.append(end_date)

            query += " ORDER BY te.start_time DESC LIMIT ?"
            params.append(limit)

            entries = db.execute_query(query, tuple(params))

            result = []
            for entry in entries:
                entry_dict = dict(entry)

                if entry_dict["duration_seconds"]:
                    entry_dict["duration_formatted"] = TimeTracker.format_duration(entry_dict["duration_seconds"])
                else:
                    if not entry_dict["end_time"]:
                        start_time = datetime.datetime.fromisoformat(entry_dict["start_time"])
                        current_time = datetime.datetime.now()
                        duration_seconds = int((current_time - start_time).total_seconds())
                        entry_dict["duration_seconds"] = duration_seconds
                        entry_dict["duration_formatted"] = TimeTracker.format_duration(duration_seconds)

                result.append(entry_dict)

            return result
        except Exception as e:
            print(f"Error getting time entries: {e}")
            return []
        finally:
            db.close()

    @staticmethod
    def get_time_summary(user_id: int, period: str = "today") -> Dict:

        db = get_db()

        try:
            today = datetime.date.today()

            if period == "today":
                start_date = today.isoformat()
                end_date = (today + datetime.timedelta(days=1)).isoformat()
            elif period == "yesterday":
                start_date = (today - datetime.timedelta(days=1)).isoformat()
                end_date = today.isoformat()
            elif period == "this_week":
                start_date = (today - datetime.timedelta(days=today.weekday())).isoformat()
                end_date = (today + datetime.timedelta(days=1)).isoformat()
            elif period == "last_week":
                start_date = (today - datetime.timedelta(days=today.weekday() + 7)).isoformat()
                end_date = (today - datetime.timedelta(days=today.weekday())).isoformat()
            elif period == "this_month":
                start_date = today.replace(day=1).isoformat()
                next_month = today.month + 1 if today.month < 12 else 1
                next_month_year = today.year if today.month < 12 else today.year + 1
                end_date = today.replace(year=next_month_year, month=next_month, day=1).isoformat()
            elif period == "last_month":
                this_month_start = today.replace(day=1)
                last_month = this_month_start.month - 1 if this_month_start.month > 1 else 12
                last_month_year = this_month_start.year if this_month_start.month > 1 else this_month_start.year - 1
                start_date = this_month_start.replace(year=last_month_year, month=last_month).isoformat()
                end_date = this_month_start.isoformat()
            else:
                start_date = today.isoformat()
                end_date = (today + datetime.timedelta(days=1)).isoformat()

            total_query = """
            SELECT SUM(duration_seconds) as total_duration
            FROM time_entries
            WHERE user_id = ? AND start_time >= ? AND start_time < ?
            AND end_time IS NOT NULL
            """

            total_result = db.execute_query(total_query, (user_id, start_date, end_date))
            total_duration = dict(total_result[0])["total_duration"] or 0

            by_task_query = """
            SELECT t.id, t.title, SUM(te.duration_seconds) as task_duration
            FROM time_entries te
            JOIN tasks t ON te.task_id = t.id
            WHERE te.user_id = ? AND te.start_time >= ? AND te.start_time < ?
            AND te.end_time IS NOT NULL
            GROUP BY t.id
            ORDER BY task_duration DESC
            """

            by_task_results = db.execute_query(by_task_query, (user_id, start_date, end_date))

            by_task = []
            for result in by_task_results:
                task_dict = dict(result)
                task_dict["duration_formatted"] = TimeTracker.format_duration(task_dict["task_duration"])
                task_dict["percentage"] = round(
                    (task_dict["task_duration"] / total_duration * 100) if total_duration > 0 else 0, 1)
                by_task.append(task_dict)

            active_entry = TimeTracker.get_active_time_entry(user_id)

            return {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "total_duration": total_duration,
                "total_duration_formatted": TimeTracker.format_duration(total_duration),
                "by_task": by_task,
                "active_entry": active_entry
            }
        except Exception as e:
            print(f"Error getting time summary: {e}")
            return {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "total_duration": 0,
                "total_duration_formatted": TimeTracker.format_duration(0),
                "by_task": [],
                "active_entry": None
            }
        finally:
            db.close()

    @staticmethod
    def format_duration(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"

        minutes, seconds = divmod(seconds, 60)
        if minutes < 60:
            return f"{minutes}m {seconds}s"

        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m {seconds}s"
