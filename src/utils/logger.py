import logging
import os
import datetime
from typing import Optional
from functools import wraps


class TimeTrackerLogger:

    def __init__(self, log_dir: str = \"logs\"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        self.setup_loggers()
    
    def ensure_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_loggers(self):

        
        self.app_logger = self._create_logger(
            \"timetracker_app\",
            os.path.join(self.log_dir, \"app.log\"),
            logging.INFO
        )
        
        self.security_logger = self._create_logger(
            \"timetracker_security\",
            os.path.join(self.log_dir, \"security.log\"),
            logging.WARNING
        )
        
        self.db_logger = self._create_logger(
            \"timetracker_db\",
            os.path.join(self.log_dir, \"database.log\"),
            logging.INFO
        )
        
        self.error_logger = self._create_logger(
            \"timetracker_errors\",
            os.path.join(self.log_dir, \"errors.log\"),
            logging.ERROR
        )
        
        self.performance_logger = self._create_logger(
            \"timetracker_performance\",
            os.path.join(self.log_dir, \"performance.log\"),
            logging.INFO
        )
    
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        \"\"\"Create a logger with specified configuration.\"\"\"
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        file_handler = logging.FileHandler(filename, encoding=\"utf-8\")
        file_handler.setLevel(level)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        formatter = logging.Formatter(
            \"%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\",
            datefmt=\"%Y-%m-%d %H:%M:%S\"
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_user_action(self, user_id: int, action: str, details: Optional[str] = None, 
                       ip_address: Optional[str] = None):
        message = f\"User {user_id} performed action: {action}\"
        if details:
            message += f\" - Details: {details}\"
        if ip_address:
            message += f\" - IP: {ip_address}\"
        
        self.app_logger.info(message)
    
    def log_security_event(self, event_type: str, user_id: Optional[int] = None, 
                          details: Optional[str] = None, ip_address: Optional[str] = None):
        message = f"Security event: {event_type}"
        if user_id:
            message += f\" - User: {user_id}\"
        if details:
            message += f\" - Details: {details}\"
        if ip_address:
            message += f\" - IP: {ip_address}\"
        
        self.security_logger.warning(message)
    
    def log_database_operation(self, operation: str, table: str, user_id: Optional[int] = None,
                              execution_time: Optional[float] = None):

        message = f\"DB Operation: {operation} on {table}\"
        if user_id:
            message += f\" - User: {user_id}\"
        if execution_time:
            message += f\" - Execution time: {execution_time:.3f}s\"
        
        self.db_logger.info(message)
    
    def log_error(self, error: Exception, context: Optional[str] = None, 
                  user_id: Optional[int] = None):

        message = f\"Error: {type(error).__name__}: {str(error)}\"
        if context:
            message += f\" - Context: {context}\"
        if user_id:
            message += f\" - User: {user_id}\"
        
        self.error_logger.error(message, exc_info=True)
    
    def log_performance(self, operation: str, execution_time: float, 
                       user_id: Optional[int] = None, details: Optional[str] = None):

        message = f\"Performance: {operation} took {execution_time:.3f}s\"
        if user_id:
            message += f\" - User: {user_id}\"
        if details:
            message += f\" - Details: {details}\"
        
        self.performance_logger.info(message)


_logger_instance = None

def get_logger() -> TimeTrackerLogger:
    global _logger_instance
    if _logger_instance is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), \"logs\")
        _logger_instance = TimeTrackerLogger(log_dir)
    return _logger_instance


def log_function_call(logger_type: str = \"app\"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = datetime.datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.datetime.now() - start_time).total_seconds()
                
                if logger_type == \"performance\":
                    logger.log_performance(
                        f\"{func.__module__}.{func.__name__}\",
                        execution_time,
                        details=f\"Args: {len(args)}, Kwargs: {len(kwargs)}\"
                    )
                else:
                    logger.app_logger.info(
                        f\"Function {func.__name__} executed successfully in {execution_time:.3f}s\"
                    )
                
                return result
            except Exception as e:
                execution_time = (datetime.datetime.now() - start_time).total_seconds()
                logger.log_error(
                    e,
                    context=f\"Function: {func.__module__}.{func.__name__}\",
                )
                raise
        
        return wrapper
    return decorator


def log_database_operation(operation: str, table: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = datetime.datetime.now()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.datetime.now() - start_time).total_seconds()
                
                logger.log_database_operation(
                    operation,
                    table,
                    execution_time=execution_time
                )
                
                return result
            except Exception as e:
                logger.log_error(
                    e,
                    context=f\"Database operation: {operation} on {table}\"
                )
                raise
        
        return wrapper
    return decorator

