import functools
import time
from typing import Type, Callable, Any
from threading import Lock

def singleton(cls: Type) -> Type:
    """Decorator to create singleton class"""
    _instances = {}
    _lock = Lock()
    
    def get_instance(*args, **kwargs) -> Any:
        with _lock:
            if cls not in _instances:
                _instances[cls] = cls(*args, **kwargs)
            return _instances[cls]
            
    return get_instance

def log_error(logger: Callable) -> Callable:
    """Decorator to log function errors"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

def throttle(delay: float) -> Callable:
    """Decorator to throttle function calls"""
    def decorator(func: Callable) -> Callable:
        last_called = 0
        _lock = Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_called
            with _lock:
                current_time = time.time()
                if current_time - last_called >= delay:
                    last_called = current_time
                    return func(*args, **kwargs)
        return wrapper
    return decorator

def async_operation(func: Callable) -> Callable:
    """Decorator to run function asynchronously"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from threading import Thread
        thread = Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread
    return wrapper

def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

def retry(max_attempts: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry failed operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator
