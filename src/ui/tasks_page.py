import streamlit as st
import datetime
import time
from src.task_management import TaskManager

def show_tasks():
    # Получаем инфо о юзере
    user_info = st.session_state.user_info
    user_id = user_info['id']
    role = user_info['role']

    # Шапка страницы
    st.markdown("## 📋 Tasks")
    st.markdown("Manage your tasks and track progress")

    # CCS
    st.markdown("""
    <style>
    .task-filters {
        background-color: #2C1338;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .task-card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 4px solid #ccc;
    }
    .task-card.priority-urgent {
        border-left-color: #F44336;
    }
    .task-card.priority-high {
        border-left-color: #FF9800;
    }
    .task-card.priority-medium {
        border-left-color: #FFC107;
    }
    .task-card.priority-low {
        border-left-color: #4CAF50;
    }
    .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .task-title {
        font-weight: 500;
        font-size: 1.1rem;
        color: black;
    }
    .task-status {
        font-size: 0.8rem;
        padding: 0.2rem 0.5rem;
        border-radius: 3px;
        color: white;
    }
    .status-not_started {
        background-color: #9E9E9E;
    }
    .status-in_progress {
        background-color: #2196F3;
    }
    .status-paused {
        background-color: #FF9800;
    }
    .status-completed {
        background-color: #4CAF50;
    }
    .status-cancelled {
        background-color: #F44336;
    }
    .task-meta {
        display: flex;
        justify-content: space-between;
        color: #777;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .task-description {
        margin-top: 0.5rem;
        font-size: 0.95rem;
        color : black;
    }
    .task-actions {
        display: flex;
        justify-content: flex-end;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Таск фильтры
    with st.container():
        st.markdown('<div class="task-filters">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            status_filter = st.selectbox(
                "Status:",
                ["All", "Not Started", "In Progress", "Paused", "Completed", "Cancelled"],
                index=0
            )

        with col2:
            priority_filter = st.selectbox(
                "Priority:",
                ["All", "Urgent", "High", "Medium", "Low"],
                index=0
            )

        with col3:
            role_filter = st.selectbox(
                "Role:",
                ["All", "Created by me", "Assigned to me"],
                index=0
            )

        with col4:
            search = st.text_input("Search:", placeholder="Task title or description")

        st.markdown('</div>', unsafe_allow_html=True)

    # Создаем новый таск
    with st.expander("➕ Create New Task"):
        col1, col2 = st.columns(2)

        with col1:
            new_task_title = st.text_input("Task Title:", key="new_task_title")
            new_task_priority = st.selectbox(
                "Priority:",
                ["low", "medium", "high", "urgent"],
                index=1,
                key="new_task_priority"
            )

            # Только для работодателя - не реализовано. Просто для вида
            if role == 'employer':
                new_task_assignee = st.selectbox(
                    "Assign To:",
                    ["Self"] + ["Employee " + str(i) for i in range(1, 5)],
                    index=0,
                    key="new_task_assignee"
                )
                assignee_id = user_id if new_task_assignee == "Self" else None
            else:
                assignee_id = user_id

        with col2:
            new_task_description = st.text_area("Description:", key="new_task_description")
            new_task_deadline = st.date_input(
                "Deadline:",
                value=None,
                min_value=datetime.date.today(),
                key="new_task_deadline"
            )
            new_task_estimated_hours = st.number_input(
                "Estimated Hours:",
                min_value=0.0,
                max_value=1000.0,
                value=1.0,
                step=0.5,
                key="new_task_estimated_hours"
            )

        if st.button("Create Task", use_container_width=True):
            if not new_task_title:
                st.error("Task title is required")
            else:
                deadline_iso = None
                if new_task_deadline:
                    deadline_iso = datetime.datetime.combine(
                        new_task_deadline,
                        datetime.time(23, 59, 59)
                    ).isoformat()

                success, message, task_id = TaskManager.create_task(
                    title=new_task_title,
                    description=new_task_description,
                    status="not_started",
                    priority=new_task_priority,
                    created_by=user_id,
                    assigned_to=assignee_id,
                    deadline=deadline_iso,
                    estimated_hours=new_task_estimated_hours
                )

                if success:
                    st.success("Task created successfully!")
                    # Перезагрузить страницу для сброса полей ввода
                    st.rerun()
                else:
                    st.error(message)

    # Таск лист

    status_map = {
        "All": None,
        "Not Started": "not_started",
        "In Progress": "in_progress",
        "Paused": "paused",
        "Completed": "completed",
        "Cancelled": "cancelled"
    }

    priority_map = {
        "All": None,
        "Urgent": "urgent",
        "High": "high",
        "Medium": "medium",
        "Low": "low"
    }

    role_map = {
        "All": "all",
        "Created by me": "creator",
        "Assigned to me": "assignee"
    }

    # Получение тасков  на основе фильтров
    tasks = TaskManager.get_tasks(
        user_id=user_id,
        status=status_map[status_filter],
        priority=priority_map[priority_filter],
        role=role_map[role_filter],
        search=search if search else None,
        limit=50
    )

    if tasks:
        for task in tasks:
            priority_class = f"priority-{task['priority']}" if task['priority'] else ""
            status_class = f"status-{task['status']}"

            deadline_str = ""
            if task['deadline']:
                deadline = datetime.datetime.fromisoformat(task['deadline'])
                deadline_str = deadline.strftime("%Y-%m-%d")

                today = datetime.date.today()
                days_left = (deadline.date() - today).days
                if days_left < 0:
                    deadline_str += " (Overdue!)"
                elif days_left == 0:
                    deadline_str += " (Today!)"
                elif days_left <= 2:
                    deadline_str += f" ({days_left} days left!)"
                else:
                    deadline_str += f" ({days_left} days left)"

            # Format status for display
            status_display = task['status'].replace('_', ' ').title()

            # Display task card
            st.markdown(f"""
            <div class="task-card {priority_class}">
                <div class="task-header">
                    <div class="task-title">{task['title']}</div>
                    <div class="task-status {status_class}">{status_display}</div>
                </div>
                <div class="task-meta">
                    <div>Priority: {task['priority'].title() if task['priority'] else 'None'}</div>
                    <div>{deadline_str}</div>
                </div>
                <div class="task-description">{task['description'] or 'No description'}</div>
                <div class="task-meta">
                    <div>Created by: {task['creator_username']}</div>
                    <div>Assigned to: {task['assignee_username'] or 'Unassigned'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Task actions
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

            with col1:
                if task['status'] not in ['completed', 'cancelled']:
                    if st.button(f"✅ Complete", key=f"complete_{task['id']}", use_container_width=True):
                        success, message = TaskManager.update_task(
                            task_id=task['id'],
                            user_id=user_id,
                            updates={'status': 'completed'}
                        )
                        if success:
                            st.success("Task marked as completed!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)

            with col2:
                if task['status'] not in ['completed', 'cancelled']:
                    if st.button(f"⏯️ {('Pause' if task['status'] == 'in_progress' else 'Resume')}", key=f"pause_{task['id']}", use_container_width=True):
                        new_status = 'paused' if task['status'] == 'in_progress' else 'in_progress'
                        success, message = TaskManager.update_task(
                            task_id=task['id'],
                            user_id=user_id,
                            updates={'status': new_status}
                        )
                        if success:
                            st.success(f"Task {new_status.replace('_', ' ')}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)

            with col3:
                if task['status'] not in ['completed', 'cancelled']:
                    if st.button(f"⏱️ Track Time", key=f"track_{task['id']}", use_container_width=True):
                        st.session_state.selected_task_for_tracking = task['id']
                        st.session_state.current_page = "Time Tracking"
                        st.rerun()

            with col4:
                if task['created_by'] == user_id and task['status'] not in ['completed', 'cancelled']:
                    if st.button(f"❌ Cancel", key=f"cancel_{task['id']}", use_container_width=True):
                        success, message = TaskManager.update_task(
                            task_id=task['id'],
                            user_id=user_id,
                            updates={'status': 'cancelled'}
                        )
                        if success:
                            st.success("Task cancelled!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
    else:
        st.info("No tasks found matching your filters.")
