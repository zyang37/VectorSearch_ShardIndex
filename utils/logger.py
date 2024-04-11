import logging
import time

class Logger:
    '''
    A class to log the time taken by a function to execute

    Log headers: timestamp, action, latency, index_name, processed_queries
    '''
    @staticmethod
    def log_index_load_time(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            logging.info(f"Func:'{func.__name__}',{elapsed_time:.8f}s,{args[1]},0")
            return result
        return wrapper
    
    @staticmethod
    def log_index_search_time(func):
        # Not need to log the args and kwargs
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            logging.info(f"Func:'{func.__name__}',{elapsed_time:.8f}s,{args[-1]},{args[1].shape[0]}")
            return result
        return wrapper

    @staticmethod
    def log_function_time(func):
        # A generic function to log the time taken by a function to execute
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            # logging.info(f"Function '{func.__name__}' executed in {elapsed_time:.4f} s with args {args} and kwargs {kwargs}")
            logging.info(f"Func:'{func.__name__}' took {elapsed_time}s with args {args} and kwargs {kwargs}")
            return result
        return wrapper
    