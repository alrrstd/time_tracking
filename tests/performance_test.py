
import time
import threading
import sqlite3
import tempfile
import os
import statistics
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from src.database.schema import Database
from src.auth.auth_manager import AuthManager
from src.task_management.task_manager import TaskManager
from src.time_tracking.time_tracker import TimeTracker


class PerformanceTestSuite:

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
            os.close(self.db_fd)
        else:
            self.db_path = db_path
        
        self.db = Database(self.db_path)
        self.results = {}
        
        import src.database
        self.original_get_db = src.database.get_db
        src.database.get_db = lambda: self.db
    
    def cleanup(self):
        import src.database
        src.database.get_db = self.original_get_db
        
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def measure_execution_time(self, func, *args, **kwargs) -> Tuple[float, any]:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return execution_time, result
    
    def test_database_operations_performance(self, num_operations: int = 1000) -> Dict:
        print(f"Testing database operations performance with {num_operations} operations...")
        
        results = {
            "insert_times": [],
            "select_times": [],
            "update_times": [],
            "delete_times": []
        }
        
        for i in range(num_operations):
            exec_time, user_id = self.measure_execution_time(
                AuthManager.register_user,
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                password="TestPassword123!",
                first_name="Test",
                last_name="User",
                role="employee"
            )
            results["insert_times"].append(exec_time)
        
        for i in range(min(100, num_operations)):
            exec_time, result = self.measure_execution_time(
                self.db.execute_query,
                "SELECT * FROM users WHERE id = ?",
                (i + 1,)
            )
            results["select_times"].append(exec_time)
        
        for i in range(min(100, num_operations)):
            exec_time, result = self.measure_execution_time(
                self.db.execute_update,
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.datetime.now().isoformat(), i + 1)
            )
            results["update_times"].append(exec_time)
        
        stats = {}
        for operation, times in results.items():
            if times:
                stats[operation] = {
                    "count": len(times),
                    "total_time": sum(times),
                    "avg_time": statistics.mean(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "median_time": statistics.median(times),
                    "std_dev": statistics.stdev(times) if len(times) > 1 else 0
                }
        
        return stats
    
    def test_concurrent_operations(self, num_threads: int = 10, operations_per_thread: int = 50) -> Dict:
        print(f"Testing concurrent operations with {num_threads} threads, {operations_per_thread} operations each...")
        
        results = {
            "thread_times": [],
            "total_operations": num_threads * operations_per_thread,
            "errors": []
        }
        
        def worker_thread(thread_id: int) -> Tuple[int, float, List[str]]:
            thread_start = time.time()
            thread_errors = []
            
            for i in range(operations_per_thread):
                try:
                    success, message, user_id = AuthManager.register_user(
                        username=f"thread{thread_id}_user{i}",
                        email=f"thread{thread_id}_user{i}@example.com",
                        password="TestPassword123!",
                        first_name="Thread",
                        last_name="User",
                        role="employee"
                    )
                    
                    if not success:
                        thread_errors.append(f"Thread {thread_id}, Op {i}: {message}")
                        continue
                    
                    success, message, task_id = TaskManager.create_task(
                        title=f"Thread {thread_id} Task {i}",
                        description="Concurrent test task",
                        status="not_started",
                        priority="medium",
                        created_by=user_id
                    )
                    
                    if not success:
                        thread_errors.append(f"Thread {thread_id}, Task {i}: {message}")
                    
                except Exception as e:
                    thread_errors.append(f"Thread {thread_id}, Op {i}: {str(e)}")
            
            thread_end = time.time()
            return thread_id, thread_end - thread_start, thread_errors
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]
            
            for future in as_completed(futures):
                thread_id, thread_time, thread_errors = future.result()
                results["thread_times"].append(thread_time)
                results["errors"].extend(thread_errors)
        
        end_time = time.time()
        
        results["total_time"] = end_time - start_time
        results["avg_thread_time"] = statistics.mean(results["thread_times"])
        results["operations_per_second"] = results["total_operations"] / results["total_time"]
        results["error_rate"] = len(results["errors"]) / results["total_operations"] * 100
        
        return results
    
    def test_memory_usage(self, num_operations: int = 1000) -> Dict:
        print(f"Testing memory usage with {num_operations} operations...")
        
        try:
            import psutil
            process = psutil.Process()
        except ImportError:
            print("psutil not available, skipping memory test")
            return {"error": "psutil not available"}
        
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples = [initial_memory]
        
        for i in range(num_operations):
            AuthManager.register_user(
                username=f"memtest{i}",
                email=f"memtest{i}@example.com",
                password="TestPassword123!",
                first_name="Memory",
                last_name="Test",
                role="employee"
            )
            
            if i % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "peak_memory_mb": max(memory_samples),
            "memory_samples": memory_samples
        }
    
    def test_time_tracking_performance(self, num_users: int = 100, num_tasks: int = 500) -> Dict:
        print(f"Testing time tracking performance with {num_users} users and {num_tasks} tasks...")
        
        setup_start = time.time()
        user_ids = []
        task_ids = []
        
        for i in range(num_users):
            success, message, user_id = AuthManager.register_user(
                username=f"timeuser{i}",
                email=f"timeuser{i}@example.com",
                password="TestPassword123!",
                first_name="Time",
                last_name="User",
                role="employee"
            )
            if success:
                user_ids.append(user_id)
        
        for i in range(num_tasks):
            user_id = user_ids[i % len(user_ids)]
            success, message, task_id = TaskManager.create_task(
                title=f"Time Task {i}",
                description="Time tracking test task",
                status="not_started",
                priority="medium",
                created_by=user_id
            )
            if success:
                task_ids.append(task_id)
        
        setup_time = time.time() - setup_start
        
        start_times = []
        stop_times = []
        query_times = []
        
        for i in range(min(100, len(user_ids), len(task_ids))):
            user_id = user_ids[i]
            task_id = task_ids[i]
            
            exec_time, result = self.measure_execution_time(
                TimeTracker.start_time_entry,
                user_id, task_id
            )
            start_times.append(exec_time)
            
            time.sleep(0.01)
            
            exec_time, result = self.measure_execution_time(
                TimeTracker.stop_time_entry,
                user_id
            )
            stop_times.append(exec_time)
            
            exec_time, result = self.measure_execution_time(
                TimeTracker.get_time_entries,
                user_id
            )
            query_times.append(exec_time)
        
        return {
            "setup_time": setup_time,
            "start_tracking_stats": {
                "count": len(start_times),
                "avg_time": statistics.mean(start_times),
                "min_time": min(start_times),
                "max_time": max(start_times)
            },
            "stop_tracking_stats": {
                "count": len(stop_times),
                "avg_time": statistics.mean(stop_times),
                "min_time": min(stop_times),
                "max_time": max(stop_times)
            },
            "query_stats": {
                "count": len(query_times),
                "avg_time": statistics.mean(query_times),
                "min_time": min(query_times),
                "max_time": max(query_times)
            }
        }
    
    def test_data_consistency(self) -> Dict:
        print("Testing data consistency and integrity...")
        
        issues = []
        
        success, message, user_id = AuthManager.register_user(
            username="consistencyuser",
            email="consistency@example.com",
            password="TestPassword123!",
            first_name="Consistency",
            last_name="User",
            role="employee"
        )
        
        if not success:
            issues.append(f"Failed to create user: {message}")
            return {"issues": issues}
        
        success, message, task_id = TaskManager.create_task(
            title="Consistency Task",
            description="Task for consistency testing",
            status="not_started",
            priority="medium",
            created_by=user_id
        )
        
        if not success:
            issues.append(f"Failed to create task: {message}")
            return {"issues": issues}
        
        start_time = datetime.datetime.now()
        success, message, entry_id = TimeTracker.start_time_entry(user_id, task_id)
        
        if not success:
            issues.append(f"Failed to start time tracking: {message}")
        else:
            entries = TimeTracker.get_time_entries(user_id)
            if entries:
                entry_start = datetime.datetime.fromisoformat(entries[0]["start_time"])
                time_diff = abs((entry_start - start_time).total_seconds())
                if time_diff > 5:
                    issues.append(f"Time zone inconsistency: {time_diff} seconds difference")
        
        try:
            success, message, bad_task_id = TaskManager.create_task(
                title="Bad Task",
                description="Task with bad user",
                status="not_started",
                priority="medium",
                created_by=99999,
                assigned_to=99999
            )
            
            if success:
                issues.append("Referential integrity violation: Created task with non-existent user")
        except Exception as e:
            pass
        
        try:
            success, message, bad_task_id = TaskManager.create_task(
                title="Invalid Status Task",
                description="Task with invalid status",
                status="invalid_status",
                priority="medium",
                created_by=user_id
            )
            
            if success:
                issues.append("Data validation failure: Created task with invalid status")
        except Exception as e:
            pass
        
        return {
            "issues": issues,
            "tests_passed": len(issues) == 0
        }
    
    def run_all_tests(self) -> Dict:
        print("Starting comprehensive performance testing...")
        
        all_results = {}
        
        try:
            all_results["database_performance"] = self.test_database_operations_performance(500)
            
            all_results["concurrent_operations"] = self.test_concurrent_operations(5, 20)
            
            all_results["memory_usage"] = self.test_memory_usage(500)
            
            all_results["time_tracking_performance"] = self.test_time_tracking_performance(50, 100)
            
            all_results["data_consistency"] = self.test_data_consistency()
            
            all_results["summary"] = {
                "total_tests": 5,
                "timestamp": datetime.datetime.now().isoformat(),
                "database_path": self.db_path
            }
            
        except Exception as e:
            all_results["error"] = str(e)
        
        return all_results


def main():
    print("Time Tracker Application - Performance Testing Suite")
    print("=" * 60)
    
    test_suite = PerformanceTestSuite()
    
    try:
        results = test_suite.run_all_tests()
        
        print("\nPerformance Test Results Summary:")
        print("=" * 40)
        
        if "database_performance" in results:
            db_perf = results["database_performance"]
            print(f"Database Operations:")
            for op, stats in db_perf.items():
                print(f"  {op}: {stats['avg_time']:.4f}s avg, {stats['count']} operations")
        
        if "concurrent_operations" in results:
            conc = results["concurrent_operations"]
            print(f"Concurrent Operations:")
            print(f"  Operations/second: {conc['operations_per_second']:.2f}")
            print(f"  Error rate: {conc['error_rate']:.2f}%")
        
        if "memory_usage" in results:
            mem = results["memory_usage"]
            if "error" not in mem:
                print(f"Memory Usage:")
                print(f"  Memory increase: {mem['memory_increase_mb']:.2f} MB")
                print(f"  Peak memory: {mem['peak_memory_mb']:.2f} MB")
        
        if "time_tracking_performance" in results:
            tt = results["time_tracking_performance"]
            print(f"Time Tracking:")
            print(f"  Start tracking: {tt['start_tracking_stats']['avg_time']:.4f}s avg")
            print(f"  Stop tracking: {tt['stop_tracking_stats']['avg_time']:.4f}s avg")
            print(f"  Query entries: {tt['query_stats']['avg_time']:.4f}s avg")
        
        if "data_consistency" in results:
            dc = results["data_consistency"]
            print(f"Data Consistency:")
            print(f"  Tests passed: {dc['tests_passed']}")
            if dc["issues"]:
                print(f"  Issues found: {len(dc['issues'])}")
                for issue in dc["issues"]:
                    print(f"    - {issue}")
        
        import json
        results_file = "performance_test_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
    finally:
        test_suite.cleanup()
    
    print("\nPerformance testing completed.")


if __name__ == "__main__":
    main()

