import datetime
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from fpdf import FPDF

from ..database.schema import get_db


class ReportingManager:

    @staticmethod
    def get_productivity_analytics(user_id: Optional[int] = None, period: str = 'week') -> Dict:

        db = get_db()

        now = datetime.datetime.now()

        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            end_date = now.isoformat()
            group_by = "%H"
            date_format = "%Y-%m-%d %H:00:00"
        elif period == 'week':
            start_date = (now - datetime.timedelta(days=7)).isoformat()
            end_date = now.isoformat()
            group_by = "%Y-%m-%d"
            date_format = "%Y-%m-%d"
        elif period == 'month':
            start_date = (now - datetime.timedelta(days=30)).isoformat()
            end_date = now.isoformat()
            group_by = "%Y-%m-%d"
            date_format = "%Y-%m-%d"
        elif period == 'year':
            start_date = (now - datetime.timedelta(days=365)).isoformat()
            end_date = now.isoformat()
            group_by = "%Y-%m"
            date_format = "%Y-%m"
        else:
            # Default to week
            start_date = (now - datetime.timedelta(days=7)).isoformat()
            end_date = now.isoformat()
            group_by = "%Y-%m-%d"
            date_format = "%Y-%m-%d"

        user_filter_clause = "" if user_id is None else "AND user_id = ?"
        user_param_tuple = (user_id,) if user_id is not None else ()

        time_query = f"""
        SELECT 
            strftime('{group_by}', start_time) as date_group,
            SUM(duration_seconds) as total_duration
        FROM time_entries
        WHERE start_time >= ? AND start_time <= ? AND end_time IS NOT NULL {user_filter_clause}
        GROUP BY date_group
        ORDER BY date_group
        """

        time_results = db.execute_query(time_query, (start_date, end_date) + user_param_tuple)

        time_by_date = []
        for result in time_results:
            result_dict = dict(result)
            time_by_date.append({
                'date': result_dict['date_group'],
                'duration_seconds': result_dict['total_duration'],
                'duration_hours': round(result_dict['total_duration'] / 3600, 2)
            })

        assigned_to_filter_clause = "" if user_id is None else "AND assigned_to = ?"
        assigned_to_param_tuple = (user_id,) if user_id is not None else ()

        tasks_query = f"""
        SELECT 
            strftime('{group_by}', completed_at) as date_group,
            COUNT(*) as completed_count
        FROM tasks
        WHERE status = 'completed' AND completed_at >= ? AND completed_at <= ? {assigned_to_filter_clause}
        GROUP BY date_group
        ORDER BY date_group
        """

        tasks_results = db.execute_query(tasks_query, (start_date, end_date) + assigned_to_param_tuple)

        tasks_by_date = []
        for result in tasks_results:
            result_dict = dict(result)
            tasks_by_date.append({
                'date': result_dict['date_group'],
                'completed_count': result_dict['completed_count']
            })

        category_query = f"""
        SELECT 
            t.priority,
            SUM(te.duration_seconds) as total_duration
        FROM time_entries te
        JOIN tasks t ON te.task_id = t.id
        WHERE te.start_time >= ? AND te.start_time <= ? AND te.end_time IS NOT NULL {user_filter_clause}
        GROUP BY t.priority
        ORDER BY total_duration DESC
        """

        category_results = db.execute_query(category_query, (start_date, end_date) + user_param_tuple)

        time_by_category = []
        for result in category_results:
            result_dict = dict(result)
            if result_dict['priority']:
                time_by_category.append({
                    'category': result_dict['priority'],
                    'duration_seconds': result_dict['total_duration'],
                    'duration_hours': round(result_dict['total_duration'] / 3600, 2)
                })


        completed_tasks = sum(task['completed_count'] for task in tasks_by_date)
        hours_worked = sum(time['duration_hours'] for time in time_by_date)
        productivity_score = (completed_tasks * 10) + hours_worked

        most_productive_day = None
        highest_score = 0

        tasks_by_date_map = {task['date']: task['completed_count'] for task in tasks_by_date}

        for time_entry in time_by_date:
            date = time_entry['date']
            hours = time_entry['duration_hours']
            tasks = tasks_by_date_map.get(date, 0)
            score = (tasks * 10) + hours

            if score > highest_score:
                highest_score = score
                most_productive_day = {
                    'date': date,
                    'hours_worked': hours,
                    'tasks_completed': tasks,
                    'score': score
                }

        return {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'time_by_date': time_by_date,
            'tasks_by_date': tasks_by_date,
            'time_by_category': time_by_category,
            'total_hours_worked': hours_worked,
            'total_tasks_completed': completed_tasks,
            'productivity_score': productivity_score,
            'most_productive_day': most_productive_day
        }

    @staticmethod
    def generate_time_report(user_id: Optional[int] = None, start_date: str = None, end_date: str = None,
                             include_details: bool = True) -> Dict:

        db = get_db()

        user_info = None
        if user_id is not None:
            user = db.execute_query(
                "SELECT username, first_name, last_name FROM users WHERE id = ?",
                (user_id,)
            )
            if not user:
                return {'error': 'User not found'}
            user_info = dict(user[0])
        else:
            user_info = {'username': 'All Users', 'first_name': 'All', 'last_name': 'Users'}

        if start_date is None:
            start_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        if end_date is None:
            end_date = datetime.datetime.now().isoformat()

        user_filter_clause = "" if user_id is None else "AND user_id = ?"
        user_param_tuple = (user_id,) if user_id is not None else ()

        summary_query = f"""
        SELECT 
            COUNT(DISTINCT te.id) as total_entries,
            SUM(te.duration_seconds) as total_duration,
            COUNT(DISTINCT te.task_id) as total_tasks
        FROM time_entries te
        WHERE te.start_time >= ? AND te.start_time <= ? AND te.end_time IS NOT NULL {user_filter_clause}
        """

        summary_result = db.execute_query(summary_query, (start_date, end_date) + user_param_tuple)
        summary = dict(summary_result[0])

        total_seconds = summary['total_duration'] or 0
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        summary['total_duration_formatted'] = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        summary['total_hours'] = round(total_seconds / 3600, 2)

        task_query = f"""
        SELECT 
            t.id,
            t.title,
            SUM(te.duration_seconds) as task_duration,
            COUNT(te.id) as entry_count
        FROM time_entries te
        JOIN tasks t ON te.task_id = t.id
        WHERE te.start_time >= ? AND te.start_time <= ? AND te.end_time IS NOT NULL {user_filter_clause}
        GROUP BY t.id
        ORDER BY task_duration DESC
        """

        task_results = db.execute_query(task_query, (start_date, end_date) + user_param_tuple)

        time_by_task = []
        for result in task_results:
            task_dict = dict(result)
            task_seconds = task_dict['task_duration']
            hours, remainder = divmod(task_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            time_by_task.append({
                'task_id': task_dict['id'],
                'task_title': task_dict['title'],
                'duration_seconds': task_seconds,
                'duration_formatted': f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                'duration_hours': round(task_seconds / 3600, 2),
                'entry_count': task_dict['entry_count'],
                'percentage': round((task_seconds / total_seconds * 100) if total_seconds > 0 else 0, 1)
            })

        day_query = f"""
        SELECT 
            strftime('%Y-%m-%d', start_time) as day,
            SUM(duration_seconds) as day_duration
        FROM time_entries
        WHERE start_time >= ? AND start_time <= ? AND end_time IS NOT NULL {user_filter_clause}
        GROUP BY day
        ORDER BY day
        """

        day_results = db.execute_query(day_query, (start_date, end_date) + user_param_tuple)

        time_by_day = []
        for result in day_results:
            day_dict = dict(result)
            day_seconds = day_dict['day_duration']

            time_by_day.append({
                'date': day_dict['day'],
                'duration_seconds': day_seconds,
                'duration_hours': round(day_seconds / 3600, 2)
            })

        detailed_entries = []
        if include_details:
            entries_query = f"""
            SELECT 
                te.id,
                te.start_time,
                te.end_time,
                te.duration_seconds,
                te.comment,
                t.id as task_id,
                t.title as task_title
            FROM time_entries te
            JOIN tasks t ON te.task_id = t.id
            WHERE te.start_time >= ? AND te.start_time <= ? AND te.end_time IS NOT NULL {user_filter_clause}
            ORDER BY te.start_time DESC
            """

            entries_results = db.execute_query(entries_query, (start_date, end_date) + user_param_tuple)

            for result in entries_results:
                entry_dict = dict(result)
                entry_seconds = entry_dict['duration_seconds']
                hours, remainder = divmod(entry_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                detailed_entries.append({
                    'id': entry_dict['id'],
                    'start_time': entry_dict['start_time'],
                    'end_time': entry_dict['end_time'],
                    'duration_seconds': entry_seconds,
                    'duration_formatted': f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                    'comment': entry_dict['comment'],
                    'task_id': entry_dict['task_id'],
                    'task_title': entry_dict['task_title']
                })

        return {
            'user': user_info,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': summary,
            'time_by_task': time_by_task,
            'time_by_day': time_by_day,
            'detailed_entries': detailed_entries
        }

    @staticmethod
    def export_report_to_csv(report_data: Dict, output_path: str) -> bool:
        """Export a time tracking report to CSV format."""
        try:
            summary_df = pd.DataFrame([{
                'User': f"{report_data['user']['first_name']} {report_data['user']['last_name']}",
                'Period Start': report_data['period']['start_date'],
                'Period End': report_data['period']['end_date'],
                'Total Hours': report_data['summary']['total_hours'],
                'Total Entries': report_data['summary']['total_entries'],
                'Total Tasks': report_data['summary']['total_tasks']
            }])

            task_df = pd.DataFrame(report_data['time_by_task'])

            day_df = pd.DataFrame(report_data['time_by_day'])

            entries_df = pd.DataFrame(report_data['detailed_entries']) if report_data['detailed_entries'] else None

            with pd.ExcelWriter(output_path) as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                task_df.to_excel(writer, sheet_name='Time by Task', index=False)
                day_df.to_excel(writer, sheet_name='Time by Day', index=False)
                if entries_df is not None:
                    entries_df.to_excel(writer, sheet_name='Detailed Entries', index=False)

            return True
        except Exception as e:
            print(f"Error exporting report to CSV: {e}")
            return False

    @staticmethod
    def export_report_to_pdf(report_data: Dict, output_path: str) -> bool:
        """

        НЕ РАБОЧЕЕ
        """
        try:
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", "B", 16)

            pdf.cell(0, 10, "Time Tracking Report", 0, 1, "C")
            pdf.ln(5)

            pdf.set_font("Arial", "B", 12)
            user_name = f"{report_data['user']['first_name']} {report_data['user']['last_name']}"
            pdf.cell(0, 10, f"User: {user_name}", 0, 1)
            pdf.cell(0, 10, f"Period: {report_data['period']['start_date']} to {report_data['period']['end_date']}", 0,
                     1)
            pdf.ln(5)


            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Summary", 0, 1)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, f"Total Time: {report_data['summary']['total_duration_formatted']}", 0, 1)
            pdf.cell(0, 10, f"Total Entries: {report_data['summary']['total_entries']}", 0, 1)
            pdf.cell(0, 10, f"Total Tasks: {report_data['summary']['total_tasks']}", 0, 1)
            pdf.ln(5)

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Time by Task", 0, 1)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(100, 10, "Task", 1)
            pdf.cell(30, 10, "Hours", 1)
            pdf.cell(30, 10, "Percentage", 1)
            pdf.cell(30, 10, "Entries", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 10)
            for task in report_data['time_by_task']:
                pdf.cell(100, 10, task['task_title'][:40], 1)
                pdf.cell(30, 10, f"{task['duration_hours']}", 1)
                pdf.cell(30, 10, f"{task['percentage']}%", 1)
                pdf.cell(30, 10, f"{task['entry_count']}", 1)
                pdf.ln()

            pdf.ln(5)

            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Time by Day", 0, 1)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, 10, "Date", 1)
            pdf.cell(30, 10, "Hours", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 10)
            for day in report_data['time_by_day']:
                pdf.cell(60, 10, day['date'], 1)
                pdf.cell(30, 10, f"{day['duration_hours']}", 1)
                pdf.ln()

            pdf.ln(5)

            if report_data['detailed_entries']:
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Detailed Entries", 0, 1)
                pdf.set_font("Arial", "B", 8)
                pdf.cell(50, 10, "Task", 1)
                pdf.cell(30, 10, "Start Time", 1)
                pdf.cell(30, 10, "End Time", 1)
                pdf.cell(20, 10, "Duration", 1)
                pdf.cell(60, 10, "Comment", 1)
                pdf.ln()

                pdf.set_font("Arial", "", 8)
                for entry in report_data['detailed_entries']:
                    pdf.cell(50, 10, entry['task_title'][:25], 1)
                    pdf.cell(30, 10, entry['start_time'], 1)
                    pdf.cell(30, 10, entry['end_time'], 1)
                    pdf.cell(20, 10, entry['duration_formatted'], 1)
                    pdf.cell(60, 10, entry['comment'][:30], 1)
                    pdf.ln()

            pdf.output(output_path)
            return True
        except Exception as e:
            print(f"Error exporting report to PDF: {e}")
            return False

