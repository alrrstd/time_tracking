import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.database import get_db, Database
from src.auth import AuthManager
from src.time_tracking import TimeTracker
from src.task_management import TaskManager
from src.calendar_integration import CalendarIntegration
from src.chat import ChatManager
from src.notifications import NotificationManager
from src.reporting import ReportingManager
from src.ui import (
    show_login_page,
    show_main_app,
    show_dashboard,
    show_time_tracking,
    show_tasks,
    show_calendar,
    show_chat,
    show_reports,
    show_settings
)

__all__ = [
    'get_db',
    'Database',
    'AuthManager',
    'TimeTracker',
    'TaskManager',
    'CalendarIntegration',
    'ChatManager',
    'NotificationManager',
    'ReportingManager',
    'show_login_page',
    'show_main_app',
    'show_dashboard',
    'show_time_tracking',
    'show_tasks',
    'show_calendar',
    'show_chat',
    'show_reports',
    'show_settings'
]
