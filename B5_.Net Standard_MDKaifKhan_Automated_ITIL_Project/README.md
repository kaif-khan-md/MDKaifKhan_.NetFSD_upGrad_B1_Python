# Smart IT Service Desk Automation System

This is my Python project for managing IT support tickets. I built this to practice OOP, file handling, exception handling, and other advanced Python concepts in a real-world style project.

---

## What This Project Does

It simulates a basic IT helpdesk system where you can:
- Raise support tickets for issues like server down, printer problems, password resets etc.
- Track the status of tickets (Open, In Progress, Closed)
- Check if tickets are within SLA time limits
- Monitor system health (CPU, RAM, Disk, Network) using psutil
- Auto-create tickets when system thresholds are breached
- Generate daily and monthly reports
- View logs of all activity

---

## How to Run

Make sure you have Python 3.10+ installed.

Install the only external library needed:
```bash
pip install psutil
```

Then just run:
```bash
python main.py
```

---

## Project Structure

```
smart_it_service_desk/
│
├── main.py         # main menu and all user interactions
├── tickets.py      # Ticket class, subclasses, TicketManager
├── monitor.py      # system monitoring using psutil
├── reports.py      # daily and monthly report generation
├── itil.py         # ITIL workflows (Incident, SR, Problem, Change)
├── utils.py        # helper functions, constants, backup to CSV
├── logger.py       # logging system, decorators, custom exceptions
├── tests.py        # unit tests
├── requirements.txt
├── README.md
│
└── data/
    ├── tickets.json    # all tickets saved here
    ├── problems.json   # ITIL records saved here
    ├── logs.txt        # all logs written here
    └── backup.csv      # CSV backup of tickets
```

---

## Ticket Types and Priority

When you create a ticket the priority is automatically assigned based on category:

| Category | Priority | SLA Limit |
|---|---|---|
| Server Down, High CPU | P1 | 1 hour |
| Internet Down, App Crash, Disk Full | P2 | 4 hours |
| Laptop Slow, Printer Issue, Outlook | P3 | 8 hours |
| Password Reset, Software Install | P4 | 24 hours |

There are 4 ticket types:
- **IncidentTicket** - for unexpected issues
- **ServiceRequest** - for standard requests
- **ProblemRecord** - auto-created when same issue happens 5+ times
- **ChangeRequest** - for planned changes to infrastructure

---

## Python Concepts Used

I tried to cover as many advanced Python concepts as possible:

**OOP**
- Base class `Ticket` with 4 subclasses using inheritance
- All attributes are private using `__` with `@property` getters (encapsulation)
- `display()` method is overridden in every subclass (polymorphism)
- Special methods: `__str__`, `__repr__`, `__eq__`, `__hash__`, `__len__`, `__bool__`, `__iter__`, `__contains__`
- Static methods and class methods (`generate_id`, `get_total_count`, `from_dict`)
- Singleton pattern in the `Logger` class

**Iterators and Generators**
- Custom `TicketIterator` class with `__iter__` and `__next__`
- `pending_tickets_generator()` in TicketManager
- `report_line_generator()` in ReportGenerator
- `sla_breach_generator()` in ITILManager
- `priority_label_generator()` in utils.py

**Functional Programming**
- `map()` to extract ticket IDs
- `filter()` to get open/closed/priority tickets
- `reduce()` from functools to count tickets by priority and department
- List comprehensions, set comprehensions, dict comprehensions throughout

**Decorators**
- `@log_call` decorator that logs every function call automatically
- `@log_ticket_event("CREATED")` parameterised decorator factory
- Both use `@wraps` to preserve function metadata

**File Handling**
- JSON read/write for tickets and ITIL records
- CSV backup using `csv.DictWriter`
- Custom context manager `SafeFileWriter` with `__enter__` and `__exit__`
- Log file appending with structured format

**Exception Handling**
- Custom exceptions: `DuplicateTicketError`, `EmptyFieldError`, `SLABreachError`, `InvalidTicketIDError`, `LogLevelError`
- `try/except/finally` blocks in all file operations and ticket CRUD
- Validation with `raise` in constructors

**Other**
- Regex for ticket ID validation (`^TKT-[A-F0-9]{8}$`), email, date
- `Counter` and `defaultdict` from collections for report analysis
- `uuid` for generating unique ticket IDs
- `psutil` for real system metrics

---

## Features by Module

**tickets.py**
- Create, search, update, close, delete tickets
- SLA checking and escalation detection
- Auto problem record creation for recurring issues
- Save/load from tickets.json

**monitor.py**
- Reads CPU, RAM, disk, network stats every check
- Compares against thresholds and raises alerts
- Auto-creates P1 incident tickets when threshold breached
- Keeps history of snapshots for average CPU calculation

**reports.py**
- Daily summary: how many tickets raised, open, closed, SLA breached
- Monthly trend: top issues, busiest department, resolution times
- Escalation report: all active breaches and alerts

**itil.py**
- Full ITIL workflow with Incident, Service Request, Problem, Change classes
- Separate from tickets.py but can scan tickets to detect problems
- Saves to problems.json separately

**logger.py**
- Singleton Logger class
- Writes to logs.txt with timestamp and level
- `stream_logs()` generator to read logs back
- `count_by_level()` using map and reduce
- Works as a context manager too

---

## Bugs I Fixed During Development

**Search/Update/Delete not working by ticket ID**
- Root cause 1: ticket IDs were stored in the index without `.upper()` on creation, but looked up with `.upper()`. Fixed by normalizing the key to uppercase everywhere in `create_ticket`, `delete_ticket`, and `__contains__`.
- Root cause 2: `if ticket:` was evaluating to `False` for tickets with 0 notes because Python was using `__len__` (which counts notes) as the truth check. Fixed by adding `__bool__` returning `True` to the `Ticket` class, and changing all checks in `main.py` to `if ticket is not None`.

---

## Sample Log Output

```
[2025-04-29 14:32:01] [INFO    ] Ticket created: TKT-3E798E6F | P1 | Server Down
[2025-04-29 14:32:45] [WARNING ] SLA Breached: TKT-3E798E6F (P1)
[2025-04-29 14:33:10] [INFO    ] Ticket TKT-3E798E6F closed.
```

---

## What I Learned

This project helped me understand how all the Python concepts fit together in a real application instead of just isolated examples. The hardest part was debugging the ticket ID lookup issue which turned out to be caused by Python using `__len__` for truth testing when `__bool__` is not defined. I also learned how decorators work internally and how to use generators to avoid loading everything into memory at once.