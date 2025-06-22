import streamlit as st
import datetime
from streamlit_calendar import calendar

from src.calendar_integration import CalendarIntegration
from src.task_management import TaskManager

def show_calendar():

    
    user_info = st.session_state.user_info
    user_id = user_info['id']
    
    st.markdown("## 📅 Calendar")
    st.markdown("View and manage your schedule and task deadlines")
    
    st.markdown("""
    <style>
    .calendar-container {
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
    .event-card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 4px solid #1E88E5;
    }
    .event-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .event-title {
        font-weight: 500;
        font-size: 1.1rem;
        color: black;
    }
    .event-time {
        color: #777;
        font-size: 0.9rem;
    }
    .event-description {
        margin-top: 0.5rem;
        font-size: 0.95rem;
        color: black;
    }
    </style>
    """, unsafe_allow_html=True)
    

    now = datetime.datetime.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month.replace(month=start_of_month.month % 12 + 1) if start_of_month.month < 12 
                    else start_of_month.replace(year=start_of_month.year + 1, month=1)) - datetime.timedelta(seconds=1)
    
    calendar_events = CalendarIntegration.get_calendar_events(
        user_id=user_id,
        start_date=start_of_month.isoformat(),
        end_date=end_of_month.isoformat()
    )
    
    tasks = TaskManager.get_tasks(
        user_id=user_id,
        status=None,
        role="all"
    )
    
    events = []
    
    for event in calendar_events:
        start_time = datetime.datetime.fromisoformat(event['start_time'])
        end_time = datetime.datetime.fromisoformat(event['end_time'])
        
        events.append({
            "id": f"event_{event['id']}",
            "title": event['title'],
            "start": event['start_time'],
            "end": event['end_time'],
            "backgroundColor": "#1E88E5",
            "borderColor": "#1976D2",
            "textColor": "#FFFFFF",
            "extendedProps": {
                "description": event['description'],
                "type": "event",
                "location": event['location']
            }
        })
    
    for task in tasks:
        if task['deadline']:
            deadline = datetime.datetime.fromisoformat(task['deadline'])
            
            if task['status'] == 'completed':
                color = "#4CAF50"
            elif task['status'] == 'cancelled':
                color = "#9E9E9E"
            elif task['priority'] == 'urgent':
                color = "#F44336"
            elif task['priority'] == 'high':
                color = "#FF9800"
            elif task['priority'] == 'medium':
                color = "#FFC107"
            else:
                color = "#8BC34A"
            
            events.append({
                "id": f"task_{task['id']}",
                "title": f"Deadline: {task['title']}",
                "start": task['deadline'],
                "allDay": True,
                "backgroundColor": color,
                "borderColor": color,
                "textColor": "#FFFFFF",
                "extendedProps": {
                    "description": task['description'],
                    "type": "task",
                    "status": task['status'],
                    "priority": task['priority']
                }
            })
    
    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "editable": False,
        "navLinks": True,
        "dayMaxEvents": True,
        "timeZone": "local",
        "height": 650
    }
    
    with st.container():
        st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
        
        calendar_data = calendar(
            events=events,
            options=calendar_options,
            key="calendar"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if calendar_data and calendar_data.get("eventClick"):
        event_id = calendar_data["eventClick"]["event"]["id"]
        event_type, entity_id = event_id.split("_")
        
        if event_type == "event":
            for event in calendar_events:
                if str(event['id']) == entity_id:
                    st.markdown("### Event Details")
                    
                    start_time = datetime.datetime.fromisoformat(event['start_time']).strftime("%Y-%m-%d %H:%M")
                    end_time = datetime.datetime.fromisoformat(event['end_time']).strftime("%Y-%m-%d %H:%M")
                    
                    st.markdown(f"""
                    <div class="event-card">
                        <div class="event-header">
                            <div class="event-title">{event['title']}</div>
                        </div>
                        <div class="event-time">From: {start_time}</div>
                        <div class="event-time">To: {end_time}</div>
                        {f'<div class="event-description">{event["description"]}</div>' if event.get('description') else ''}
                        {f'<div style = "color : black;" class="event-location">Location: {event["location"]}</div>' if event.get('location') else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit Event", key=f"edit_{event['id']}", use_container_width=True):
                            st.session_state.edit_event_id = event['id']
                            st.rerun()
                    with col2:
                        if st.button("Delete Event", key=f"delete_{event['id']}", use_container_width=True):
                            success, message = CalendarIntegration.delete_calendar_event(int(entity_id), user_id)
                            if success:
                                st.success("Event deleted successfully!")
                                st.rerun()
                            else:
                                st.error(message)
                    break
        
        elif event_type == "task":
            for task in tasks:
                if str(task['id']) == entity_id:
                    st.markdown("### Task Details")
                    
                    deadline = datetime.datetime.fromisoformat(task['deadline']).strftime("%Y-%m-%d")
                    
                    status_display = task['status'].replace('_', ' ').title()
                    
                    st.markdown(f"""
                    <div class="event-card">
                        <div class="event-header">
                            <div class="event-title">{task['title']}</div>
                            <div>{status_display}</div>
                        </div>
                        <div class="event-time">Deadline: {deadline}</div>
                        <div>Priority: {task['priority'].title() if task['priority'] else 'None'}</div>
                        {f'<div class="event-description">{task["description"]}</div>' if task.get('description') else ''}
                        <div>Created by: {task['creator_username']}</div>
                        <div>Assigned to: {task['assignee_username'] or 'Unassigned'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("View Task", key=f"view_{task['id']}", use_container_width=True):
                            st.session_state.current_page = "Tasks"
                            st.session_state.selected_task_id = task['id']
                            st.rerun()
                    with col2:
                        if task['status'] not in ['completed', 'cancelled']:
                            if st.button("Track Time", key=f"track_{task['id']}", use_container_width=True):
                                st.session_state.current_page = "Time Tracking"
                                st.session_state.selected_task_for_tracking = task['id']
                                st.rerun()
                    break
    
    with st.expander("➕ Add New Event"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_title = st.text_input("Event Title:", key="new_event_title")
            event_start_date = st.date_input(
                "Start Date:",
                value=datetime.date.today(),
                key="new_event_start_date"
            )
            event_start_time = st.time_input(
                "Start Time:",
                value=datetime.time(9, 0),
                key="new_event_start_time"
            )
            event_location = st.text_input("Location (optional):", key="new_event_location")
        
        with col2:
            event_description = st.text_area("Description (optional):", key="new_event_description")
            event_end_date = st.date_input(
                "End Date:",
                value=datetime.date.today(),
                key="new_event_end_date"
            )
            event_end_time = st.time_input(
                "End Time:",
                value=datetime.time(10, 0),
                key="new_event_end_time"
            )
            
            tasks_with_deadlines = [task for task in tasks if task['deadline'] and task['status'] not in ['completed', 'cancelled']]
            
            if tasks_with_deadlines:
                task_options = {f"{task['id']}: {task['title']}": task['id'] for task in tasks_with_deadlines}
                task_options["None"] = None
                selected_task = st.selectbox("Link to Task (optional):", options=list(task_options.keys()), index=len(task_options)-1)
                task_id = task_options[selected_task] if selected_task != "None" else None
            else:
                task_id = None
        
        if st.button("Add Event", use_container_width=True):
            if not event_title:
                st.error("Event title is required")
            else:
                start_datetime = datetime.datetime.combine(event_start_date, event_start_time)
                end_datetime = datetime.datetime.combine(event_end_date, event_end_time)
                
                if end_datetime <= start_datetime:
                    st.error("End time must be after start time")
                else:
                    success, message, event_id = CalendarIntegration.add_calendar_event(
                        user_id=user_id,
                        title=event_title,
                        description=event_description,
                        start_time=start_datetime.isoformat(),
                        end_time=end_datetime.isoformat(),
                        location=event_location,
                        task_id=task_id
                    )
                    
                    if success:
                        st.success("Event added successfully!")
                        st.session_state.new_event_title = ""
                        st.session_state.new_event_description = ""
                        st.session_state.new_event_location = ""
                        st.rerun()
                    else:
                        st.error(message)
    
    with st.expander("🔄 Sync Tasks with Calendar"):
        st.markdown("Create calendar events for tasks with deadlines")
        
        tasks_to_sync = []
        for task in tasks:
            if task['deadline'] and task['status'] not in ['completed', 'cancelled']:
                has_event = False
                for event in calendar_events:
                    if event.get('task_id') == task['id']:
                        has_event = True
                        break
                
                if not has_event:
                    tasks_to_sync.append(task)
        
        if tasks_to_sync:
            st.markdown("Select tasks to create calendar events for:")
            
            selected_tasks = []
            for task in tasks_to_sync:
                deadline = datetime.datetime.fromisoformat(task['deadline']).strftime("%Y-%m-%d")
                if st.checkbox(f"{task['title']} (Deadline: {deadline})", key=f"sync_{task['id']}"):
                    selected_tasks.append(task['id'])
            
            if st.button("Sync Selected Tasks", use_container_width=True):
                if selected_tasks:
                    synced_count = 0
                    for task_id in selected_tasks:
                        success, _, _ = CalendarIntegration.sync_task_with_calendar(task_id, user_id)
                        if success:
                            synced_count += 1
                    
                    if synced_count > 0:
                        st.success(f"Successfully synced {synced_count} tasks with calendar!")
                        st.rerun()
                    else:
                        st.warning("No tasks were synced. Please try again.")
                else:
                    st.warning("Please select at least one task to sync")
        else:
            st.info("All tasks with deadlines are already synced with your calendar.")
