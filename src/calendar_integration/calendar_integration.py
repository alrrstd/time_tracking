
import datetime
from typing import Dict, List, Optional, Tuple

from ..database import get_db


class CalendarIntegration:

    @staticmethod
    def add_calendar_event(user_id: int, title: str, description: Optional[str],
                          start_time: str, end_time: str, location: Optional[str] = None,
                          task_id: Optional[int] = None, calendar_source: str = 'internal',
                          external_id: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        """

        Возврашаем кортеж (success, message, event_id).
        """
        db = get_db()
        
        if not title or len(title.strip()) < 3:
            return False, "Event title must be at least 3 characters long", None
            
        try:
            datetime.datetime.fromisoformat(start_time)
            datetime.datetime.fromisoformat(end_time)
            
            if task_id:
                task = db.execute_query(
                    "SELECT id FROM tasks WHERE id = ?", 
                    (task_id,)
                )
                
                if not task:
                    return False, "Task not found", None
            
            event_id = db.execute_insert(
                """
                INSERT INTO calendar_events (user_id, task_id, title, description, 
                                           start_time, end_time, location, 
                                           calendar_source, external_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, task_id, title, description, start_time, end_time, 
                 location, calendar_source, external_id, datetime.datetime.now().isoformat())
            )
            
            return True, "Calendar event added successfully", event_id
        except ValueError:
            return False, "Invalid date format", None
        except Exception as e:
            return False, f"Failed to add calendar event: {str(e)}", None
    
    @staticmethod
    def update_calendar_event(event_id: int, user_id: int, updates: Dict) -> Tuple[bool, str]:
        """
        Возвращаем кортеж (success, message).
        """
        db = get_db()
        
        event = db.execute_query(
            "SELECT id FROM calendar_events WHERE id = ? AND user_id = ?",
            (event_id, user_id)
        )
        
        if not event:
            return False, "Calendar event not found or you don't have permission to update it"
        
        update_fields = []
        params = []
        
        for field, value in updates.items():
            if field in ['title', 'description', 'start_time', 'end_time', 'location']:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if 'task_id' in updates:
            if updates['task_id']:
                task = db.execute_query(
                    "SELECT id FROM tasks WHERE id = ?", 
                    (updates['task_id'],)
                )
                
                if not task:
                    return False, "Task not found"
                
                update_fields.append("task_id = ?")
                params.append(updates['task_id'])
        
        if not update_fields:
            return False, "No valid fields to update"
        
        try:
            params.append(event_id)
            
            db.execute_update(
                f"UPDATE calendar_events SET {', '.join(update_fields)} WHERE id = ?",
                tuple(params)
            )
            
            return True, "Calendar event updated successfully"
        except Exception as e:
            return False, f"Failed to update calendar event: {str(e)}"
    
    @staticmethod
    def delete_calendar_event(event_id: int, user_id: int) -> Tuple[bool, str]:

        db = get_db()
        
        event = db.execute_query(
            "SELECT id FROM calendar_events WHERE id = ? AND user_id = ?",
            (event_id, user_id)
        )
        
        if not event:
            return False, "Calendar event not found or you don't have permission to delete it"
        
        try:
            db.execute_update(
                "DELETE FROM calendar_events WHERE id = ?",
                (event_id,)
            )
            
            return True, "Calendar event deleted successfully"
        except Exception as e:
            return False, f"Failed to delete calendar event: {str(e)}"
    
    @staticmethod
    def get_calendar_events(user_id: int, start_date: Optional[str] = None, 
                           end_date: Optional[str] = None, task_id: Optional[int] = None) -> List[Dict]:
        db = get_db()
        
        query = """
        SELECT ce.*, t.title as task_title
        FROM calendar_events ce
        LEFT JOIN tasks t ON ce.task_id = t.id
        WHERE ce.user_id = ?
        """
        params = [user_id]
        
        if start_date:
            query += " AND ce.end_time >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND ce.start_time <= ?"
            params.append(end_date)
        
        if task_id:
            query += " AND ce.task_id = ?"
            params.append(task_id)
        
        query += " ORDER BY ce.start_time"
        
        events = db.execute_query(query, tuple(params))
        
        result = []
        for event in events:
            result.append(dict(event))
        
        return result
    
    @staticmethod
    def sync_task_with_calendar(task_id: int, user_id: int) -> Tuple[bool, str, Optional[int]]:

        db = get_db()
        
        task = db.execute_query(
            "SELECT id, title, description, deadline FROM tasks WHERE id = ? AND (created_by = ? OR assigned_to = ?)",
            (task_id, user_id, user_id)
        )
        
        if not task:
            return False, "Task not found or you don't have permission to access it", None
        
        task_data = dict(task[0])
        
        if not task_data['deadline']:
            return False, "Task has no deadline to sync with calendar", None
        
        existing_event = db.execute_query(
            "SELECT id FROM calendar_events WHERE task_id = ? AND user_id = ?",
            (task_id, user_id)
        )
        
        if existing_event:
            return False, "Calendar event already exists for this task", dict(existing_event[0])['id']
        
        deadline = datetime.datetime.fromisoformat(task_data['deadline'])
        
        end_time = (deadline + datetime.timedelta(hours=1)).isoformat()
        
        return CalendarIntegration.add_calendar_event(
            user_id=user_id,
            title=f"Deadline: {task_data['title']}",
            description=task_data['description'],
            start_time=task_data['deadline'],
            end_time=end_time,
            task_id=task_id,
            calendar_source='internal'
        )
    
    @staticmethod
    def get_upcoming_events(user_id: int, days: int = 7) -> List[Dict]:
        now = datetime.datetime.now()
        end_date = (now + datetime.timedelta(days=days)).isoformat()
        
        return CalendarIntegration.get_calendar_events(
            user_id=user_id,
            start_date=now.isoformat(),
            end_date=end_date
        )
