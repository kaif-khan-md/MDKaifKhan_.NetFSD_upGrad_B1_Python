"""
logger.py - Centralized Logging Module
Supports INFO, WARNING, ERROR, CRITICAL levels.
Writes to logs.txt with structured format.
Uses decorators, context managers, and generators.

"""

import os
import re
from datetime import datetime
from functools import wraps

DATA_DIR = "data"
LOG_FILE  = os.path.join(DATA_DIR, "logs.txt")
os.makedirs(DATA_DIR, exist_ok=True)


#  Log Levels

LOG_LEVELS = {
    "DEBUG":    0,
    "INFO":     1,
    "WARNING":  2,
    "ERROR":    3,
    "CRITICAL": 4,
}


# Custom Exceptions

class LogLevelError(Exception):
    """Raised when an invalid log level is used."""
    pass

class DuplicateTicketError(Exception):
    """Raised when a duplicate ticket ID is detected."""
    pass

class InvalidTicketIDError(Exception):
    """Raised for malformed ticket IDs."""
    pass

class EmptyFieldError(Exception):
    """Raised when a required field is blank."""
    pass

class SLABreachError(Exception):
    """Raised when SLA is breached."""
    pass


#  Core Logger Class
class Logger:
    """
    Singleton logger for the IT Service Desk.
    Demonstrates: encapsulation, static methods, special methods,
    context managers, decorators, generators.
    """
    _instance = None  # singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        self.__log_file = LOG_FILE
        self.__min_level = "INFO"
        self.__initialized = True

    def __repr__(self):
        return f"Logger(file={self.__log_file}, min_level={self.__min_level})"

    def __str__(self):
        return f"[Logger] → {self.__log_file}"

    # Context Manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.critical(f"Exception in context: {exc_type.__name__}: {exc_val}")
        return False  # don't suppress exceptions

    # Core write
    def _write(self, level: str, message: str):
        level = level.upper()
        if level not in LOG_LEVELS:
            raise LogLevelError(f"Invalid log level: '{level}'. Must be one of {list(LOG_LEVELS.keys())}")
        if LOG_LEVELS[level] < LOG_LEVELS[self.__min_level]:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level:<8}] {message}\n"
        try:
            with open(self.__log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except IOError as e:
            print(f"Logger write failed: {e}")

    # Public methods
    def info(self, msg: str):     self._write("INFO", msg)
    def warning(self, msg: str):  self._write("WARNING", msg)
    def error(self, msg: str):    self._write("ERROR", msg)
    def critical(self, msg: str): self._write("CRITICAL", msg)
    def debug(self, msg: str):    self._write("DEBUG", msg)

    @staticmethod
    def get_log_path() -> str:
        return LOG_FILE

    def set_min_level(self, level: str):
        level = level.upper()
        if level not in LOG_LEVELS:
            raise LogLevelError(f"Invalid level: {level}")
        self.__min_level = level

    # Generator: stream log lines
    def stream_logs(self, level_filter: str | None = None):
        """
        Generator that yields log lines, optionally filtered by level.
        Demonstrates: generators (yield).
        """
        pattern = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\s*\] (.+)")
        try:
            with open(self.__log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    match = pattern.match(line)
                    if match:
                        ts, lvl, msg = match.groups()
                        if level_filter is None or lvl.strip() == level_filter.upper():
                            yield {"timestamp": ts, "level": lvl.strip(), "message": msg}
                    else:
                        if level_filter is None:
                            yield {"timestamp": "", "level": "RAW", "message": line}
        except FileNotFoundError:
            return  # empty generator

    def get_recent_logs(self, n: int = 50, level_filter: str | None = None) -> list[dict]:
        """Read last N log entries using the stream_logs generator."""
        all_logs = list(self.stream_logs(level_filter))
        return all_logs[-n:]

    def count_by_level(self) -> dict:
        """
        Use map + filter + reduce to count log entries per level.
        Demonstrates: map, filter, reduce.
        """
        from functools import reduce
        entries = list(self.stream_logs())
        levels = list(map(lambda e: e["level"], entries))
        result = reduce(
            lambda acc, lvl: {**acc, lvl: acc.get(lvl, 0) + 1},
            levels,
            {}
        )
        return result

    def search_logs(self, keyword: str) -> list[dict]:
        """Filter logs by keyword using list comprehension."""
        return [e for e in self.stream_logs() if keyword.lower() in e["message"].lower()]

    def print_recent(self, n: int = 30, level_filter: str | None = None):
        entries = self.get_recent_logs(n, level_filter)
        if not entries:
            print("  No log entries found.")
            return
        print(f"\n{'─'*65}")
        header = f"  LAST {len(entries)} LOG ENTRIES"
        header += f" (level={level_filter})" if level_filter else ""
        print(header)
        print(f"{'─'*65}")
        icons = {"INFO": "ℹ️ ", "WARNING": "⚠️ ", "ERROR": "❌", "CRITICAL": "🔥", "DEBUG": "🔍", "RAW": "  "}
        for e in entries:
            icon = icons.get(e["level"], "  ")
            print(f"  {icon} [{e['timestamp']}] [{e['level']:<8}] {e['message']}")
        print(f"{'─'*65}")

    def clear_logs(self):
        """Wipe the log file (use carefully)."""
        with open(self.__log_file, "w") as f:
            f.write("")
        self.info("Log file cleared by administrator.")


#  Decorator: log function calls automatically

_logger = Logger()

def log_call(func):
    """
    Decorator that logs every function call with args and result.
    Demonstrates: decorators, *args/**kwargs, wraps.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        _logger.debug(f"CALL → {func.__module__}.{func.__name__}()")
        try:
            result = func(*args, **kwargs)
            _logger.debug(f"OK   ← {func.__name__}() returned {type(result).__name__}")
            return result
        except Exception as e:
            _logger.error(f"FAIL ← {func.__name__}() raised {type(e).__name__}: {e}")
            raise
    return wrapper


def log_ticket_event(event_type: str):
    """
    Parameterised decorator factory for specific ticket events.
    Usage: @log_ticket_event("CREATED")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            _logger.info(f"TICKET {event_type}: {func.__name__}() executed")
            return result
        return wrapper
    return decorator


#  Module-level convenience functions

def log_event(level: str, message: str):
    """Convenience wrapper used across all modules."""
    level = level.upper()
    if level == "INFO":      _logger.info(message)
    elif level == "WARNING": _logger.warning(message)
    elif level == "ERROR":   _logger.error(message)
    elif level == "CRITICAL":_logger.critical(message)
    else:                    _logger.debug(message)

# Expose the singleton
get_logger = lambda: _logger