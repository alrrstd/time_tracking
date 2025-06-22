
import streamlit as st
import datetime
import time
from streamlit_autorefresh import st_autorefresh

from src.time_tracking import TimeTracker
from src.task_management import TaskManager

def show_time_tracking():

    user_info = st.session_state.user_info
    user_id = user_info['id']

    # Инициализация  таймера
    if 'timer_active' not in st.session_state:
        st.session_state.timer_active = False
    if 'timer_start_time' not in st.session_state:
        st.session_state.timer_start_time = None
    if 'timer_base_seconds' not in st.session_state:
        st.session_state.timer_base_seconds = 0
    if 'page_visible' not in st.session_state:
        st.session_state.page_visible = True

    st.markdown("## ⏱️ Time Tracking")
    st.markdown("Track your time efficiently and stay productive")

    st.markdown("""
    <style>
    .timer-container {
        background-color: #2C1338;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .timer-display {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        color: #1E88E5;
        margin: 1rem 0;
        font-family: 'Courier New', monospace;
        transition: color 0.3s ease;
    }
    .timer-display.running {
        color: #4CAF50;
        text-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
        animation: pulse 2s infinite;
    }
    .timer-display.paused {
        color: #FF9800;
        text-shadow: 0 0 10px rgba(255, 152, 0, 0.3);
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    .timer-task {
        font-size: 1.2rem;
        font-weight: 500;
        text-align: center;
        margin-bottom: 1rem;
    }
    .timer-buttons {
        display: flex;
        justify-content: center;
        gap: 1rem;
    }
    .entries-container {
        margin-top: 2rem;
    }
    .entry-card {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .entry-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .entry-title {
        font-weight: 500;
        color: black;
    }
    .entry-time {
        color: #777;
        font-size: 0.9rem;
    }
    .entry-duration {
        font-weight: 500;
        color: #1E88E5;
    }
    .page-status {
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8rem;
        z-index: 1000;
        background-color: rgba(76, 175, 80, 0.2);
        color: #4CAF50;
        border: 1px solid #4CAF50;
    }
    .page-status.hidden {
        background-color: rgba(255, 152, 0, 0.2);
        color: #FF9800;
        border: 1px solid #FF9800;
    }
    .refresh-info {
        position: fixed;
        bottom: 10px;
        right: 10px;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.7rem;
        z-index: 1000;
        background-color: rgba(33, 150, 243, 0.1);
        color: #2196F3;
        border: 1px solid #2196F3;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- JavaScript для отслеживания видимости страницы ---
    # st.markdown("""
    # <div class="page-status" id="pageStatus">Страница активна</div>
    # <script>
    # let isPageVisible = true;
    #
    # // Определяем правильные имена событий для разных браузеров
    # let hidden, visibilityChange;
    # if (typeof document.hidden !== "undefined") {
    #     hidden = "hidden";
    #     visibilityChange = "visibilitychange";
    # } else if (typeof document.msHidden !== "undefined") {
    #     hidden = "msHidden";
    #     visibilityChange = "msvisibilitychange";
    # } else if (typeof document.webkitHidden !== "undefined") {
    #     hidden = "webkitHidden";
    #     visibilityChange = "webkitvisibilitychange";
    # }
    #
    # function handleVisibilityChange() {
    #     isPageVisible = !document[hidden];
    #     const statusElement = document.getElementById('pageStatus');
    #
    #     if (isPageVisible) {
    #         statusElement.textContent = 'Страница активна';
    #         statusElement.className = 'page-status';
    #         // Сохраняем состояние в localStorage
    #         localStorage.setItem('pageVisible', 'true');
    #     } else {
    #         statusElement.textContent = 'Страница неактивна';
    #         statusElement.className = 'page-status hidden';
    #         localStorage.setItem('pageVisible', 'false');
    #     }
    # }
    #
    # if (typeof document[hidden] !== "undefined") {
    #     document.addEventListener(visibilityChange, handleVisibilityChange, false);
    # }
    #
    # // Дополнительные события для лучшей совместимости
    # window.addEventListener('focus', () => {
    #     isPageVisible = true;
    #     handleVisibilityChange();
    # });
    # window.addEventListener('blur', () => {
    #     isPageVisible = false;
    #     handleVisibilityChange();
    # });
    #
    # // Инициализация при загрузке
    # handleVisibilityChange();
    #
    # // Глобальная функция для проверки видимости
    # window.getPageVisibility = function() {
    #     return localStorage.getItem('pageVisible') !== 'false';
    # };
    # </script>
    # """, unsafe_allow_html=True)

    active_entry = TimeTracker.get_active_time_entry(user_id)

    refresh_interval = None
    if active_entry and st.session_state.timer_active:
        # Обновляем каждую секунду только если таймер активен
        refresh_interval = 1000  # 1 секунда в миллисекундах

    # Автообновление с помощью streamlit-autorefresh
    if refresh_interval:
        # Проверяем видимость страницы через JavaScript
        page_visible_js = st.markdown("""
        <script>
        const pageVisible = window.getPageVisibility ? window.getPageVisibility() : true;
        if (!pageVisible) {
            // Если страница не видима, не обновляем
            window.skipRefresh = true;
        } else {
            window.skipRefresh = false;
        }
        </script>
        """, unsafe_allow_html=True)

        # Используем autorefresh только если страница видима
        count = st_autorefresh(interval=refresh_interval, limit=None, key="timer_refresh") # НЕ ИСПОЛЬЗОВАЛОСЬ

        # Показываем информацию об обновлениях
        #st.markdown(f'<div class="refresh-info">Обновлений: {count}</div>', unsafe_allow_html=True)# НЕ ИСПОЛЬЗОВАЛОСЬ

    with st.container():
        st.markdown('<div class="timer-container">', unsafe_allow_html=True)

        if active_entry:
            st.markdown(f'<div class="timer-task">Currently tracking: {active_entry["task_title"]}</div>', unsafe_allow_html=True)

            # Инициализируем таймер если он еще не активен
            if not st.session_state.timer_active:
                st.session_state.timer_active = True
                st.session_state.timer_start_time = time.time()
                st.session_state.timer_base_seconds = active_entry['duration_seconds']

            # Вычисляем текущее время
            if st.session_state.timer_start_time:
                current_elapsed = int(time.time() - st.session_state.timer_start_time)
                total_seconds = st.session_state.timer_base_seconds + current_elapsed
            else:
                total_seconds = st.session_state.timer_base_seconds

            # Отображаем таймер с анимацией
            timer_class = "timer-display running"
            st.markdown(
                f'<div class="{timer_class}">{format_time(total_seconds)}</div>',
                unsafe_allow_html=True
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⏸️ Pause", use_container_width=True):
                    # Обновляем базовое время и останавливаем таймер
                    if st.session_state.timer_start_time:
                        current_elapsed = int(time.time() - st.session_state.timer_start_time)
                        st.session_state.timer_base_seconds += current_elapsed
                        st.session_state.timer_start_time = None
                        st.session_state.timer_active = False

                    success, message, time_entry_data = TimeTracker.pause_time_entry(user_id)
                    if success:
                        st.success(f"Time tracking paused. Duration: {time_entry_data['duration_formatted']}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

            with col2:
                if st.button("⏹️ Stop", use_container_width=True):
                    # Останавливаем таймер
                    st.session_state.timer_active = False
                    st.session_state.timer_start_time = None
                    st.session_state.timer_base_seconds = 0

                    comment = st.text_area("Add a comment (optional):", value=active_entry.get('comment', ''))

                    if st.button("Confirm Stop", use_container_width=True):
                        success, message, time_entry_data = TimeTracker.stop_time_entry(user_id, comment)
                        if success:
                            st.success(f"Time tracking stopped. Duration: {time_entry_data['duration_formatted']}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)

        else:
            # Сбрасываем состояние таймера
            st.session_state.timer_active = False
            st.session_state.timer_start_time = None
            st.session_state.timer_base_seconds = 0

            st.markdown('<div class="timer-task">Start tracking a new task</div>', unsafe_allow_html=True)
            st.markdown('<div class="timer-display">00:00:00</div>', unsafe_allow_html=True)

            tasks = TaskManager.get_tasks(
                user_id=user_id,
                status="not_started,in_progress,paused",
                role="all"
            )

            if tasks:
                task_options = {f"{task['id']}: {task['title']}": task['id'] for task in tasks}
                selected_task = st.selectbox("Select a task:", options=list(task_options.keys()))

                task_id = task_options[selected_task] if selected_task else None

                comment = st.text_area("Add a comment (optional):")

                if st.button("▶️ Start Tracking", use_container_width=True):
                    if task_id:
                        success, message, time_entry_id = TimeTracker.start_time_entry(user_id, task_id, comment)
                        if success:
                            # Инициализируем таймер
                            st.session_state.timer_active = True
                            st.session_state.timer_start_time = time.time()
                            st.session_state.timer_base_seconds = 0

                            st.success("Time tracking started!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please select a task")
            else:
                st.warning("No active tasks found. Create or assign tasks in the Tasks section.")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Recent Time Entries")

    recent_entries = TimeTracker.get_time_entries(user_id, limit=10)

    if recent_entries:
        for entry in recent_entries:
            start_time = datetime.datetime.fromisoformat(entry['start_time']).strftime("%Y-%m-%d %H:%M")

            if entry.get('end_time'):
                end_time = datetime.datetime.fromisoformat(entry['end_time']).strftime("%H:%M")
                time_range = f"{start_time} - {end_time}"
            else:
                time_range = f"{start_time} - In progress"

            duration = entry.get('duration_formatted', 'In progress')

            st.markdown(f"""
            <div class="entry-card">
                <div class="entry-header">
                    <span class="entry-title">{entry['task_title']}</span>
                    <span class="entry-duration">{duration}</span>
                </div>
                <div class="entry-time">{time_range}</div>
                {f'<div class="entry-comment">{entry["comment"]}</div>' if entry.get('comment') else ''}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent time entries found. Start tracking your time!")

    st.markdown("### Time Summary")

    period_options = {
        "today": "Today",
        "yesterday": "Yesterday",
        "this_week": "This Week",
        "last_week": "Last Week",
        "this_month": "This Month",
        "last_month": "Last Month"
    }

    col1, col2 = st.columns([1, 3])
    with col1:
        selected_period = st.selectbox("Period:", options=list(period_options.values()), index=2)

    period_key = list(period_options.keys())[list(period_options.values()).index(selected_period)]

    summary = TimeTracker.get_time_summary(user_id, period_key)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Time", summary['total_duration_formatted'])
    with col2:
        st.metric("Tasks Worked On", len(summary['by_task']))
    with col3:
        if period_key in ['this_week', 'last_week']:
            days = 7
            daily_avg = round(summary['total_duration'] / days / 3600, 1)
            st.metric("Daily Average", f"{daily_avg} hours")
        elif period_key in ['this_month', 'last_month']:
            days = 30
            daily_avg = round(summary['total_duration'] / days / 3600, 1)
            st.metric("Daily Average", f"{daily_avg} hours")
        else:
            st.metric("Period", period_options[period_key])

    if summary['by_task']:
        st.markdown("#### Time by Task")

        for task in summary['by_task']:
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <div>{task['title']}</div>
                <div style="display: flex; gap: 1rem;">
                    <div style="width: 80px; text-align: right;">{task['duration_formatted']}</div>
                    <div style="width: 50px; text-align: right;">{task['percentage']}%</div>
                </div>
            </div>
            <div style="height: 10px; background-color: #eee; border-radius: 5px; margin-bottom: 1rem;">
                <div style="height: 100%; width: {task['percentage']}%; background-color: #1E88E5; border-radius: 5px;"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(f"No time entries found for {period_options[period_key].lower()}.")

def format_time(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

