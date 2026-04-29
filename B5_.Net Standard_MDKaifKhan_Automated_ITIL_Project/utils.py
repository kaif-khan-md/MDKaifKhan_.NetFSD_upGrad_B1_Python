"""
utils.py - Shared utilities, constants, helpers, backup

Advanced Python: 
    map, filter, reduce, list comprehensions,
    regex, generators, context managers, string handling.
"""

import os
import csv
import json
import re
from datetime import datetime
from functools import reduce

# Paths

DATA_DIR     = "data"
LOG_FILE     = os.path.join(DATA_DIR, "logs.txt")
BACKUP_CSV   = os.path.join(DATA_DIR, "backup.csv")
TICKETS_FILE = os.path.join(DATA_DIR, "tickets.json")
os.makedirs(DATA_DIR, exist_ok=True)


# Priority & SLA constants

PRIORITY_MAP: dict = {
    "Server Down":       "P1",
    "High CPU Usage":    "P1",
    "Internet Down":     "P2",
    "Disk Space Full":   "P2",
    "Application Crash": "P2",
    "Laptop Slow":       "P3",
    "Printer Issue":     "P3",
    "Outlook Issue":     "P3",
    "Password Reset":    "P4",
    "Software Install":  "P4",
    "Other":             "P4",
}

SLA_HOURS: dict = {"P1": 1, "P2": 4, "P3": 8, "P4": 24}
ESCALATION_MINUTES: dict = {"P1": 30, "P2": 120}

CATEGORY_MAP: dict = {
    "1":  "Server Down",
    "2":  "Internet Down",
    "3":  "High CPU Usage",
    "4":  "Application Crash",
    "5":  "Disk Space Full",
    "6":  "Laptop Slow",
    "7":  "Printer Issue",
    "8":  "Outlook Issue",
    "9":  "Password Reset",
    "10": "Software Install",
    "11": "Other",
}

TICKET_TYPE_MAP: dict = {
    "1": "Incident",
    "2": "ServiceRequest",
    "3": "ProblemRecord",
    "4": "ChangeRequest",
}

DEPARTMENTS: list = [
    "IT", "HR", "Finance", "Sales", "Operations",
    "Marketing", "Legal", "Admin", "Engineering", "Support"
]

STATUS_OPTIONS: dict = {"1": "Open", "2": "In Progress", "3": "Closed"}


# Regex Patterns

TICKET_ID_PATTERN = re.compile(r"^TKT-[A-F0-9]{8}$")
EMAIL_PATTERN     = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")
DATE_PATTERN      = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_ticket_id(tid: str) -> bool:
    return bool(TICKET_ID_PATTERN.match(tid.strip().upper()))


def validate_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_date(date_str: str) -> bool:
    return bool(DATE_PATTERN.match(date_str.strip()))


# Generator: priority info

def priority_label_generator():
    """Generator that yields (priority, label, sla) tuples."""
    priority_info = [
        ("P1", "Critical", "1 Hour"),
        ("P2", "High",     "4 Hours"),
        ("P3", "Medium",   "8 Hours"),
        ("P4", "Low",      "24 Hours"),
    ]
    for item in priority_info:
        yield item


# map / filter / reduce helpers

def filter_open_tickets(tickets: list) -> list:
    return list(filter(lambda t: t.status == "Open", tickets))


def map_to_ids(tickets: list) -> list:
    return list(map(lambda t: t.ticket_id, tickets))


def count_by_priority(tickets: list) -> dict:
    return reduce(
        lambda acc, t: {**acc, t.priority: acc.get(t.priority, 0) + 1},
        tickets, {}
    )


def get_categories_set(tickets: list) -> set:
    return {t.category for t in tickets}


# Context Manager: safe file writer

class SafeFileWriter:
    """Context manager for safe file writes with automatic logging."""

    def __init__(self, filepath: str, mode: str = "w"):
        self.__filepath = filepath
        self.__mode     = mode
        self.__file     = None

    def __enter__(self):
        try:
            self.__file = open(self.__filepath, self.__mode, encoding="utf-8")
            return self.__file
        except IOError as e:
            log_event("ERROR", f"SafeFileWriter failed to open {self.__filepath}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__file:
            self.__file.close()
        if exc_type:
            log_event("ERROR", f"Exception during file write to {self.__filepath}: {exc_val}")
        return False


# Backup (CSV)

def backup_tickets_to_csv() -> bool:
    """Backup tickets.json to backup.csv using context manager."""
    try:
        if not os.path.exists(TICKETS_FILE):
            print("No tickets.json found to backup.")
            return False

        with open(TICKETS_FILE, "r", encoding="utf-8") as f:
            tickets = json.load(f)

        if not tickets:
            print("No tickets to backup.")
            return False

        fieldnames = [
            "ticket_id", "employee_name", "department", "issue_description",
            "category", "priority", "status", "ticket_type",
            "created_at", "updated_at", "closed_at", "sla_breached"
        ]

        with SafeFileWriter(BACKUP_CSV, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(tickets)

        log_event("INFO", f"Backup created: {BACKUP_CSV} ({len(tickets)} records)")
        print(f"Backup saved to {BACKUP_CSV} ({len(tickets)} records)")
        return True

    except FileNotFoundError as e:
        log_event("ERROR", f"Backup failed - file not found: {e}")
        print(f"File not found: {e}")
    except json.JSONDecodeError as e:
        log_event("ERROR", f"Backup failed - JSON error: {e}")
        print(f"JSON error: {e}")
    except Exception as e:
        log_event("ERROR", f"Backup failed: {e}")
        print(f"Backup error: {e}")
    return False


# Logging (module-level wrapper, delegates to logger.py)

def log_event(level: str, message: str):
    """Convenience wrapper - avoids circular import."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level.upper():<8}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


# String Handling helpers

def truncate(s: str, n: int = 20) -> str:
    return s[:n - 1] + "…" if len(s) > n else s


def pad_right(s: str, n: int) -> str:
    return str(s).ljust(n)


def format_priority_badge(priority: str) -> str:
    badges = {"P1": "P1-Critical", "P2": "P2-High",
              "P3": "P3-Medium",   "P4": "P4-Low"}
    return badges.get(priority, priority)


def format_status_badge(status: str) -> str:
    return status


# UI Helpers

def print_header(title: str):
    w = 100
    print("\n" + "-" * w)
    print(f"  {title.upper()}")
    print("-" * w)


def print_separator():
    print("-" * 100)


def select_from_list(label: str, options: dict) -> str:
    print(f"\n  {label}:")
    for k, v in options.items():
        print(f"    {k}. {v}")
    while True:
        choice = input("  Enter number: ").strip()
        if choice in options:
            return options[choice]
        print("  Invalid choice. Try again.")


def input_non_empty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("  This field cannot be empty.")


def view_logs(last_n: int = 30):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        print(f"\n{'-'*58}")
        print(f"  LAST {min(last_n, len(lines))} LOG ENTRIES")
        print(f"{'-'*58}")
        for line in lines[-last_n:]:
            print(" ", line.rstrip())
    except FileNotFoundError:
        print("  No logs found yet.")


def ascii_bar(percent: float, width: int = 28) -> str:
    filled = int((min(percent, 100) / 100) * width)
    empty  = width - filled
    icon   = "[HIGH]" if percent > 85 else ("[MED]" if percent > 60 else "[OK]")
    return f"[{'#' * filled}{'-' * empty}] {percent:5.1f}%  {icon}"