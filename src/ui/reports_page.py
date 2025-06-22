import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import os

from src.reporting import ReportingManager
from src.time_tracking import TimeTracker
from src.task_management import TaskManager
from src.database.schema import get_db

def show_reports():

    user_info = st.session_state.user_info
    current_user_id = user_info["id"]
    role = user_info["role"]

    st.markdown("## 📊 Reports & Analytics")
    st.markdown("Analyze productivity and generate detailed reports")

    st.markdown("""
    <style>
    .report-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .metric-card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .metric-label {
        color: #777;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["Productivity Analytics", "Time Reports", "Task Reports", "Export Reports"])

    # Админ в проекте до конца не реализован
    selected_user_id = None
    if role == "admin":
        db = get_db()
        users = db.execute_query("SELECT id, username, first_name, last_name FROM users")
        user_options = {"All Users": None}
        for user in users:
            user_options[f"{user["first_name"]} {user["last_name"]} ({user["username"]})"] = user["id"]

        selected_user_name = st.selectbox("Select User for Report:", options=list(user_options.keys()))
        selected_user_id = user_options[selected_user_name]
    else:
        selected_user_id = current_user_id

    with tabs[0]:
        st.markdown("### Productivity Analytics")

        period_options = {
            "day": "Today",
            "week": "This Week",
            "month": "This Month",
            "year": "This Year"
        }

        col1, col2 = st.columns([1, 3])
        with col1:
            selected_period = st.selectbox("Period:", options=list(period_options.values()), index=1, key="productivity_period_select")

        period_key = list(period_options.keys())[list(period_options.values()).index(selected_period)]

        analytics = ReportingManager.get_productivity_analytics(selected_user_id, period_key)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.1f}</div>
                <div class="metric-label">Hours Worked</div>
            </div>
            """.format(analytics["total_hours_worked"]), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Tasks Completed</div>
            </div>
            """.format(analytics["total_tasks_completed"]), unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{:.1f}</div>
                <div class="metric-label">Productivity Score</div>
            </div>
            """.format(analytics["productivity_score"]), unsafe_allow_html=True)

        with col4:
            most_productive = analytics["most_productive_day"]
            if most_productive:
                day_display = most_productive["date"]
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">{}</div>
                    <div class="metric-label">Most Productive Day</div>
                </div>
                """.format(day_display), unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="metric-card">
                    <div class="metric-value">-</div>
                    <div class="metric-label">Most Productive Day</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("#### Time Tracking")

        if analytics["time_by_date"]:
            df = pd.DataFrame(analytics["time_by_date"])

            fig = px.bar(
                df,
                x="date",
                y="duration_hours",
                title="Hours Tracked by Date",
                labels={"duration_hours": "Hours", "date": "Date"},
                color="duration_hours",
                color_continuous_scale="blues"
            )

            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No time tracking data available for {selected_period.lower()}.")

        st.markdown("#### Task Completion")

        if analytics["tasks_by_date"]:
            df = pd.DataFrame(analytics["tasks_by_date"])

            fig = px.bar(
                df,
                x="date",
                y="completed_count",
                title="Tasks Completed by Date",
                labels={"completed_count": "Tasks", "date": "Date"},
                color="completed_count",
                color_continuous_scale="greens"
            )

            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No task completion data available for {selected_period.lower()}.")

        st.markdown("#### Time by Priority")

        if analytics["time_by_category"]:
            df = pd.DataFrame(analytics["time_by_category"])

            fig = px.pie(
                df,
                values="duration_hours",
                names="category",
                title="Time Distribution by Priority",
                color="category",
                color_discrete_map={
                    "urgent": "#F44336",
                    "high": "#FF9800",
                    "medium": "#FFC107",
                    "low": "#4CAF50"
                }
            )

            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No category data available for {selected_period.lower()}.")


    with tabs[1]:
        st.markdown("### Time Reports")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date:",
                value=datetime.date.today() - datetime.timedelta(days=7),
                key="time_report_start_date"
            )
        with col2:
            end_date = st.date_input(
                "End Date:",
                value=datetime.date.today(),
                key="time_report_end_date"
            )

        start_date_iso = datetime.datetime.combine(start_date, datetime.time.min).isoformat()
        end_date_iso = datetime.datetime.combine(end_date, datetime.time.max).isoformat()

        include_details = st.checkbox("Include detailed entries", value=True, key="time_report_include_details")

        if st.button("Generate Time Report", use_container_width=True, key="generate_time_report_button"):
            # Generate report
            report_data = ReportingManager.generate_time_report(
                user_id=selected_user_id,
                start_date=start_date_iso,
                end_date=end_date_iso,
                include_details=include_details
            )

            if "error" in report_data:
                st.error(report_data["error"])
            else:
                st.markdown("#### Report Summary")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Hours", f"{report_data["summary"]["total_hours"]:.2f}")
                with col2:
                    st.metric("Total Entries", report_data["summary"]["total_entries"])
                with col3:
                    st.metric("Total Tasks", report_data["summary"]["total_tasks"])

                st.markdown("#### Time by Task")

                if report_data["time_by_task"]:
                    df = pd.DataFrame(report_data["time_by_task"])
                    df = df[["task_title", "duration_hours", "percentage", "entry_count"]]
                    df.columns = ["Task", "Hours", "Percentage", "Entries"]

                    st.dataframe(df, use_container_width=True)

                    fig = px.pie(
                        df,
                        values="Hours",
                        names="Task",
                        title="Time Distribution by Task"
                    )

                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No time entries found for the selected period.")

                st.markdown("#### Time by Day")

                if report_data["time_by_day"]:
                    df = pd.DataFrame(report_data["time_by_day"])

                    fig = px.bar(
                        df,
                        x="date",
                        y="duration_hours",
                        title="Hours Tracked by Day",
                        labels={"duration_hours": "Hours", "date": "Date"},
                        color="duration_hours",
                        color_continuous_scale="blues"
                    )

                    fig.update_layout(
                        height=400,
                        margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        coloraxis_showscale=False
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No daily data available for the selected period.")

                if include_details and report_data["detailed_entries"]:
                    st.markdown("#### Detailed Entries")

                    df = pd.DataFrame(report_data["detailed_entries"])

                    df["start_time"] = pd.to_datetime(df["start_time"]).dt.strftime("%Y-%m-%d %H:%M")
                    df["end_time"] = pd.to_datetime(df["end_time"]).dt.strftime("%Y-%m-%d %H:%M")

                    df = df[["task_title", "start_time", "end_time", "duration_formatted", "comment"]]
                    df.columns = ["Task", "Start Time", "End Time", "Duration", "Comment"]

                    st.dataframe(df, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Export to Excel", use_container_width=True, key="export_excel_button"):
                        export_dir = os.path.join(os.getcwd(), "exports")
                        os.makedirs(export_dir, exist_ok=True)

                        filename = f"time_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx"
                        filepath = os.path.join(export_dir, filename)

                        success = ReportingManager.export_report_to_csv(report_data, filepath)

                        if success:
                            st.success(f"Report exported to {filepath}")
                        else:
                            st.error("Failed to export report")

                with col2:
                    if st.button("Export to PDF", use_container_width=True, key="export_pdf_button"):
                        export_dir = os.path.join(os.getcwd(), "exports")
                        os.makedirs(export_dir, exist_ok=True)

                        filename = f"time_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf"
                        filepath = os.path.join(export_dir, filename)

                        success = ReportingManager.export_report_to_pdf(report_data, filepath)

                        if success:
                            st.success(f"Report exported to {filepath}")
                        else:
                            st.error("Failed to export report")

    with tabs[2]:
        st.markdown("### Task Reports")

        task_stats = TaskManager.get_task_statistics(selected_user_id)

        st.markdown("#### Task Status Distribution")

        status_labels = ["Not Started", "In Progress", "Paused", "Completed", "Cancelled"]
        status_values = [
            task_stats["status_counts"]["not_started"],
            task_stats["status_counts"]["in_progress"],
            task_stats["status_counts"]["paused"],
            task_stats["status_counts"]["completed"],
            task_stats["status_counts"]["cancelled"]
        ]

        df = pd.DataFrame({
            "Status": status_labels,
            "Count": status_values
        })

        fig = px.pie(
            df,
            values="Count",
            names="Status",
            title="Task Status Distribution",
            color="Status",
            color_discrete_map={
                "Not Started": "#9E9E9E",
                "In Progress": "#2196F3",
                "Paused": "#FF9800",
                "Completed": "#4CAF50",
                "Cancelled": "#F44336"
            }
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Task Priority Distribution")

        priority_labels = ["Urgent", "High", "Medium", "Low"]
        priority_values = [
            task_stats["priority_counts"]["urgent"],
            task_stats["priority_counts"]["high"],
            task_stats["priority_counts"]["medium"],
            task_stats["priority_counts"]["low"]
        ]

        df = pd.DataFrame({
            "Priority": priority_labels,
            "Count": priority_values
        })

        fig = px.pie(
            df,
            values="Count",
            names="Priority",
            title="Task Priority Distribution",
            color="Priority",
            color_discrete_map={
                "Urgent": "#F44336",
                "High": "#FF9800",
                "Medium": "#FFC107",
                "Low": "#4CAF50"
            }
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.markdown("### Export Reports")

        st.write("Select options to export reports.")

        export_user_id = None
        if role == "admin":
            db = get_db()
            users = db.execute_query("SELECT id, username, first_name, last_name FROM users")
            export_user_options = {"All Users": None}
            for user in users:
                export_user_options[f"{user["first_name"]} {user["last_name"]} ({user["username"]})"] = user["id"]

            selected_export_user_name = st.selectbox("Select User for Export:", options=list(export_user_options.keys()), key="export_user_select")
            export_user_id = export_user_options[selected_export_user_name]
        else:
            export_user_id = current_user_id

        col1, col2 = st.columns(2)
        with col1:
            export_start_date = st.date_input(
                "Start Date for Export:",
                value=datetime.date.today() - datetime.timedelta(days=30),
                key="export_start_date"
            )
        with col2:
            export_end_date = st.date_input(
                "End Date for Export:",
                value=datetime.date.today(),
                key="export_end_date"
            )

        export_start_date_iso = datetime.datetime.combine(export_start_date, datetime.time.min).isoformat()
        export_end_date_iso = datetime.datetime.combine(export_end_date, datetime.time.max).isoformat()

        export_include_details = st.checkbox("Include detailed entries in export", value=True, key="export_include_details")

        if st.button("Generate and Export Report", use_container_width=True, key="generate_export_button"):
            report_data = ReportingManager.generate_time_report(
                user_id=export_user_id,
                start_date=export_start_date_iso,
                end_date=export_end_date_iso,
                include_details=export_include_details
            )

            if "error" in report_data:
                st.error(report_data["error"])
            else:
                export_format = st.radio("Select Export Format:", ("Excel", "PDF"), key="export_format_radio")

                export_dir = os.path.join(os.getcwd(), "exports")
                os.makedirs(export_dir, exist_ok=True)

                if export_format == "Excel":
                    filename = f"time_report_{export_user_id if export_user_id else 'all_users'}_{export_start_date.strftime("%Y%m%d")}_{export_end_date.strftime("%Y%m%d")}.xlsx"
                    filepath = os.path.join(export_dir, filename)
                    success = ReportingManager.export_report_to_csv(report_data, filepath)
                    if success:
                        st.success(f"Report exported to {filepath}")
                        with open(filepath, "rb") as f:
                            st.download_button(
                                label="Download Excel Report",
                                data=f,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.error("Failed to export report to Excel")
                elif export_format == "PDF":
                    filename = f"time_report_{export_user_id if export_user_id else 'all_users'}_{export_start_date.strftime("%Y%m%d")}_{export_end_date.strftime("%Y%m%d")}.pdf"
                    filepath = os.path.join(export_dir, filename)
                    success = ReportingManager.export_report_to_pdf(report_data, filepath)
                    if success:
                        st.success(f"Report exported to {filepath}")
                        with open(filepath, "rb") as f:
                            st.download_button(
                                label="Download PDF Report",
                                data=f,
                                file_name=filename,
                                mime="application/pdf"
                            )
                    else:
                        st.error("Failed to export report to PDF")

