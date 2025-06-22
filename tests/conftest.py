import pytest
import os
import tempfile
import sqlite3
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.database.schema import Database
from src.auth.auth_manager import AuthManager
from src.task_management.task_manager import TaskManager
from src.time_tracking.time_tracker import TimeTracker


@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    db = Database(db_path)
    
    yield db
    
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_db():
    mock_db = Mock()
    mock_db.execute_query.return_value = []
    mock_db.execute_insert.return_value = 1
    mock_db.execute_update.return_value = 1
    mock_db.close.return_value = None
    return mock_db


@pytest.fixture
def sample_user_data():
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "first_name": "Test",
        "last_name": "User",
        "role": "employee",
        "created_at": "2025-01-01T00:00:00",
        "last_login": None,
        "is_active": 1
    }


@pytest.fixture
def sample_task_data():
    return {
        "id": 1,
        "title": "Test Task",
        "description": "This is a test task",
        "status": "not_started",
        "priority": "medium",
        "created_by": 1,
        "assigned_to": 1,
        "created_at": "2025-01-01T00:00:00",
        "deadline": "2025-01-31T23:59:59",
        "completed_at": None,
        "estimated_hours": 8.0
    }


@pytest.fixture
def sample_time_entry_data():
    return {
        "id": 1,
        "user_id": 1,
        "task_id": 1,
        "start_time": "2025-01-01T09:00:00",
        "end_time": "2025-01-01T17:00:00",
        "duration_seconds": 28800,  # 8 hours
        "comment": "Worked on test task",
        "created_at": "2025-01-01T09:00:00"
    }


@pytest.fixture
def authenticated_user():
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "employee",
        "first_name": "Test",
        "last_name": "User",
        "token": "mock_jwt_token"
    }


@pytest.fixture(autouse=True)
def mock_get_db(mock_db):
    with patch("src.database.get_db", return_value=mock_db):
        yield mock_db


@pytest.fixture
def mock_streamlit():
    with patch("streamlit.session_state") as mock_session_state, \
         patch("streamlit.error") as mock_error, \
         patch("streamlit.success") as mock_success, \
         patch("streamlit.warning") as mock_warning, \
         patch("streamlit.info") as mock_info:
        
        mock_session_state.user_info = {
            "id": 1,
            "username": "testuser",
            "role": "employee"
        }
        
        yield {
            "session_state": mock_session_state,
            "error": mock_error,
            "success": mock_success,
            "warning": mock_warning,
            "info": mock_info
        }


class TestDataFactory:

    @staticmethod
    def create_user(username="testuser", email="test@example.com", role="employee", **kwargs):
        user_data = {
            "username": username,
            "email": email,
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "role": role
        }
        user_data.update(kwargs)
        return user_data
    
    @staticmethod
    def create_task(title="Test Task", created_by=1, **kwargs):
        task_data = {
            "title": title,
            "description": "This is a test task",
            "status": "not_started",
            "priority": "medium",
            "created_by": created_by,
            "assigned_to": created_by,
            "deadline": "2025-12-31T23:59:59",
            "estimated_hours": 8.0
        }
        task_data.update(kwargs)
        return task_data
    
    @staticmethod
    def create_time_entry(user_id=1, task_id=1, **kwargs):
        time_entry_data = {
            "user_id": user_id,
            "task_id": task_id,
            "start_time": "2025-01-01T09:00:00",
            "end_time": "2025-01-01T17:00:00",
            "duration_seconds": 28800,
            "comment": "Test work session"
        }
        time_entry_data.update(kwargs)
        return time_entry_data


@pytest.fixture
def test_data_factory():
    return TestDataFactory

