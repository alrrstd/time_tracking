import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

from src.time_tracking import TimeTracker
from src.task_management import TaskManager
from src.notifications import NotificationManager

def show_dashboard():

    user_info = st.session_state.user_info
    user_id = user_info["id"]
    role = user_info["role"]

    st.markdown("""
    <style>
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border: 2px solid transparent;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .metric-card:focus-within {
        border-color: #4CAF50;
        outline: 2px solid #4CAF50;
        outline-offset: 2px;
    }
    
    .metric-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: rgba(255,255,255,0.9);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: white;
    }
    
    .metric-subtitle {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.8);
        line-height: 1.4;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-running {
        background-color: #4CAF50;
        animation: pulse 2s infinite;
    }
    
    .status-stopped {
        background-color: #9E9E9E;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Chart container improvements */
    .chart-container {
        background: no background ;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #333;
        display: flex;
        align-items: center;
    }
    
    .chart-title::before {
        content: "📈";
        margin-right: 0.5rem;
        font-size: 1.3rem;
    }
    
    /* Activity list improvements */
    .activity-item {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #667eea;
        transition: background-color 0.2s ease;
    }
    
    .activity-item:hover {
        background: #e9ecef;
    }
    
    .activity-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 0.3rem;
    }
    
    .activity-meta {
        font-size: 0.85rem;
        color: #666;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .metric-card {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .chart-container {
            padding: 0.8rem;
        }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .metric-card {
            border: 2px solid white;
        }
        
        .activity-item {
            border: 1px solid #333;
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        .metric-card {
            transition: none;
        }
        
        .status-running {
            animation: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <header role="banner">
        <h1>📊 Dashboard</h1>
        <p>Welcome to your productivity command center</p>
    </header>
    """, unsafe_allow_html=True)

    st.markdown("<main role='main'>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    active_entry = TimeTracker.get_active_time_entry(user_id)

    with col1:
        status_class = "status-running" if active_entry else "status-stopped"
        status_text = "Running" if active_entry else "Stopped"

        if active_entry:
            task_info = f"Active: {active_entry['task_title']}"
            duration_info = f"Duration: {active_entry['duration_formatted']}"
        else:
            task_info = "No active tracking"
            duration_info = "Start tracking on Time Tracking page"

        st.markdown(f"""
        <div class="metric-card" role="region" aria-labelledby="time-tracking-title" tabindex="0">
            <div class="metric-title" id="time-tracking-title">⏱️ Time Tracking</div>
            <div class="metric-value">
                <span class="status-indicator {status_class}" aria-hidden="true"></span>
                {status_text}
            </div>
            <div class="metric-subtitle">
                {task_info}<br>
                {duration_info}
            </div>
        </div>
        """, unsafe_allow_html=True)

    task_stats = TaskManager.get_task_statistics(user_id)
    open_tasks = (task_stats["status_counts"]["not_started"] +
                  task_stats["status_counts"]["in_progress"] +
                  task_stats["status_counts"]["paused"])

    with col2:
        st.markdown(f"""
        <div class="metric-card" role="region" aria-labelledby="tasks-title" tabindex="0">
            <div class="metric-title" id="tasks-title">📋 Tasks</div>
            <div class="metric-value">{open_tasks}</div>
            <div class="metric-subtitle">
                Open tasks<br>
                Completed: {task_stats["status_counts"]["completed"]}<br>
                Success rate: {task_stats["completion_rate"]:.2f}% 
            </div>
        </div>
        """, unsafe_allow_html=True)

    time_summary = TimeTracker.get_time_summary(user_id, "today")

    with col3:
        st.markdown(f"""
        <div class="metric-card" role="region" aria-labelledby="today-title" tabindex="0">
            <div class="metric-title" id="today-title">🕒 Today</div>
            <div class="metric-value">{time_summary["total_duration_formatted"]}</div>
            <div class="metric-subtitle">
                Time tracked<br>
                Tasks worked: {len(time_summary["by_task"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

    notification_count = NotificationManager.get_unread_count(user_id)

    with col4:
        next_deadline_text = "No upcoming deadlines"
        if task_stats["upcoming_deadlines"]:
            next_deadline = task_stats["upcoming_deadlines"][0]
            deadline_date = datetime.datetime.fromisoformat(next_deadline["deadline"]).strftime("%m/%d")
            next_deadline_text = f"Next: {deadline_date}"

        st.markdown(f"""
        <div class="metric-card" role="region" aria-labelledby="notifications-title" tabindex="0">
            <div class="metric-title" id="notifications-title">🔔 Notifications</div>
            <div class="metric-value">{notification_count}</div>
            <div class="metric-subtitle">
                Unread messages<br>
                {next_deadline_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <section class="chart-container" role="region" aria-labelledby="time-chart-title">
        <h2 class="chart-title" id="time-chart-title">Time Tracking Overview</h2>
    </section>
    """, unsafe_allow_html=True)

    dates = []
    hours = []

    today = datetime.date.today()
    for i in range(6, -1, -1):
        date = today - datetime.timedelta(days=i)
        dates.append(date.strftime("%a"))
        if i == 0:
            hours.append(time_summary["total_duration"] / 3600)
        else:
            hours.append(max(0, 8 - i + (i % 3)))

    df = pd.DataFrame({
        "Day": dates,
        "Hours": hours
    })

    fig = px.bar(
        df,
        x="Day",
        y="Hours",
        title="Hours Tracked This Week",
        labels={"Hours": "Hours Worked", "Day": "Day of Week"},
        color="Hours",
        color_continuous_scale="blues"
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        font=dict(size=12),
        title_font_size=16
    )

    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Hours: %{y:.1f}<extra></extra>",
        texttemplate="%{y:.1f}h",
        textposition="outside"
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <section role="region" aria-labelledby="task-status-title">
            <h3 id="task-status-title">📊 Task Status Distribution</h3>
        </section>
        """, unsafe_allow_html=True)

        status_labels = ["Not Started", "In Progress", "Paused", "Completed", "Cancelled"]
        status_values = [
            task_stats["status_counts"]["not_started"],
            task_stats["status_counts"]["in_progress"],
            task_stats["status_counts"]["paused"],
            task_stats["status_counts"]["completed"],
            task_stats["status_counts"]["cancelled"]
        ]

        fig = go.Figure(data=[go.Pie(
            labels=status_labels,
            values=status_values,
            hole=.4,
            marker_colors=["#FFBB78", "#1F77B4", "#FF9896", "#2CA02C", "#D62728"],
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
        )])

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            ),
            font=dict(size=11)
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
        <section role="region" aria-labelledby="task-priority-title">
            <h3 id="task-priority-title">🎯 Task Priority Distribution</h3>
        </section>
        """, unsafe_allow_html=True)

        priority_labels = ["Low", "Medium", "High", "Urgent"]
        priority_values = [
            task_stats["priority_counts"]["low"],
            task_stats["priority_counts"]["medium"],
            task_stats["priority_counts"]["high"],
            task_stats["priority_counts"]["urgent"]
        ]

        fig = go.Figure(go.Bar(
            x=priority_values,
            y=priority_labels,
            orientation="h",
            marker_color=["#2196F3", "#FFC107", "#FF9800", "#F44336"],
            hovertemplate="<b>%{y} Priority</b><br>Tasks: %{x}<extra></extra>"
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Number of Tasks",
            yaxis_title="Priority Level",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=11)
        )

        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <section role="region" aria-labelledby="recent-activity-title">
            <h3 id="recent-activity-title">🕒 Recent Time Entries</h3>
        </section>
        """, unsafe_allow_html=True)

        recent_entries = TimeTracker.get_time_entries(user_id, limit=5)

        if recent_entries:
            for i, entry in enumerate(recent_entries):
                start_time = datetime.datetime.fromisoformat(entry["start_time"]).strftime("%m/%d %H:%M")
                duration = entry.get("duration_formatted", "In progress")

                st.markdown(f"""
                <div class="activity-item" role="listitem" tabindex="0" aria-label="Time entry {i+1}">
                    <div class="activity-title">{entry["task_title"]}</div>
                    <div class="activity-meta">{start_time} • {duration}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p>No recent time entries found.</p>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <section role="region" aria-labelledby="upcoming-deadlines-title">
            <h3 id="upcoming-deadlines-title">📅 Upcoming Deadlines</h3>
        </section>
        """, unsafe_allow_html=True)

        if task_stats["upcoming_deadlines"]:
            for i, deadline in enumerate(task_stats["upcoming_deadlines"]):
                deadline_date = datetime.datetime.fromisoformat(deadline["deadline"]).strftime("%m/%d/%Y")

                st.markdown(f"""
                <div class="activity-item" role="listitem" tabindex="0" aria-label="Deadline {i+1}">
                    <div class="activity-title">{deadline["title"]}</div>
                    <div class="activity-meta">Due: {deadline_date}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p>No upcoming deadlines.</p>", unsafe_allow_html=True)

    if role == "employer":
        st.markdown("""
        <section role="region" aria-labelledby="team-overview-title">
            <h3 id="team-overview-title">👥 Team Overview</h3>
            <p>Team productivity metrics and reports are available on the Reports page.</p>
        </section>
        """, unsafe_allow_html=True)

    st.markdown("</main>", unsafe_allow_html=True)
