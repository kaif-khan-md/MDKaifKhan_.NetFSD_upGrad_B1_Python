"""
tickets.py - Ticket Management System
OOP: Ticket (base), IncidentTicket, ServiceRequest, ProblemRecord, ChangeRequest
Advanced: Iterators, Generators, Decorators, map/filter/reduce,
          Encapsulation, Inheritance, Polymorphism, Static/Class methods,
          Special methods (__str__, __repr__, __eq__, __len__, __iter__)
File Handling: JSON read/write, CSV backup, context managers
Exception Handling: try/except/finally, raise, custom exceptions
"""

import json
import uuid
from datetime import datetime
from collections import Counter
from functools import reduce

from utils import (log_event, PRIORITY_MAP, SLA_HOURS, ESCALATION_MINUTES,
                   TICKETS_FILE, backup_tickets_to_csv)
from logger import (log_call, log_ticket_event,
                    DuplicateTicketError, InvalidTicketIDError,
                    EmptyFieldError, SLABreachError)


#  BASE CLASS: Ticket

class Ticket:
    """
    Base ticket class.
    Demonstrates: Encapsulation, constructors, instance variables,
    static/class methods, special methods, properties.
    """
    _ticket_counter: int = 0   # class variable

    def __init__(self, employee_name: str, department: str,
                 issue_description: str, category: str):
        # ── Validation (raise + custom exceptions) ──
        if not issue_description or not issue_description.strip():
            raise EmptyFieldError("Issue description cannot be empty.")
        if not employee_name or not employee_name.strip():
            raise EmptyFieldError("Employee name cannot be empty.")

        Ticket._ticket_counter += 1

        # Private instance variables (Encapsulation)
        self.__ticket_id        = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        self.__employee_name    = employee_name.strip()
        self.__department       = department.strip()
        self.__issue_description = issue_description.strip()
        self.__category         = category
        self.__priority         = PRIORITY_MAP.get(category, "P4")
        self.__status           = "Open"
        self.__created_at       = datetime.now().isoformat()
        self.__updated_at       = self.__created_at
        self.__closed_at: str | None = None
        self.__sla_breached     = False
        self.__ticket_type      = "General"
        self.__notes: list[str] = []

    # Special Methods
    def __str__(self):
        return (f"[{self.__ticket_id}] {self.__priority} | "
                f"{self.__status} | {self.__employee_name} | {self.__category}")

    def __repr__(self):
        return (f"Ticket(id={self.__ticket_id!r}, "
                f"priority={self.__priority!r}, status={self.__status!r})")

    def __eq__(self, other):
        return isinstance(other, Ticket) and self.__ticket_id == other.ticket_id

    def __hash__(self):
        return hash(self.__ticket_id)

    def __len__(self):
        """Return number of notes."""
        return len(self.__notes)

    def __bool__(self):
        return True 

    # Properties (Encapsulation)
    @property
    def ticket_id(self):          return self.__ticket_id
    @property
    def employee_name(self):      return self.__employee_name
    @property
    def department(self):         return self.__department
    @property
    def issue_description(self):  return self.__issue_description
    @property
    def category(self):           return self.__category
    @property
    def priority(self):           return self.__priority
    @property
    def status(self):             return self.__status
    @property
    def created_at(self):         return self.__created_at
    @property
    def updated_at(self):         return self.__updated_at
    @property
    def closed_at(self):          return self.__closed_at
    @property
    def sla_breached(self):       return self.__sla_breached
    @property
    def ticket_type(self):        return self.__ticket_type
    @property
    def notes(self):              return list(self.__notes)

    @status.setter
    def status(self, value: str):
        allowed = {"Open", "In Progress", "Closed"}
        if value not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        self.__status     = value
        self.__updated_at = datetime.now().isoformat()
        if value == "Closed":
            self.__closed_at = datetime.now().isoformat()

    @sla_breached.setter
    def sla_breached(self, value: bool):
        self.__sla_breached = value

    # Allow subclasses to set ticket_type
    def _set_type(self, t: str):
        self.__ticket_type = t

    # Business Methods
    def add_note(self, note: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.__notes.append(f"[{ts}] {note}")

    def check_sla(self) -> bool:
        """Returns True if SLA is breached."""
        if self.__status == "Closed":
            return False
        elapsed_hours = (datetime.now() -
                         datetime.fromisoformat(self.__created_at)).total_seconds() / 3600
        sla_limit = SLA_HOURS.get(self.__priority, 24)
        if elapsed_hours > sla_limit:
            self.__sla_breached = True
            return True
        return False

    def check_escalation(self) -> str | None:
        """Returns escalation message if threshold exceeded."""
        if self.__status == "Closed":
            return None
        elapsed_min = (datetime.now() -
                       datetime.fromisoformat(self.__created_at)).total_seconds() / 60
        if self.__priority == "P1" and elapsed_min > ESCALATION_MINUTES["P1"]:
            return (f"[ESCALATION] {self.__ticket_id} (P1) "
                    f"unresolved for {elapsed_min:.0f} min!")
        if self.__priority == "P2" and elapsed_min > ESCALATION_MINUTES["P2"]:
            return (f"[ESCALATION] {self.__ticket_id} (P2) "
                    f"unresolved for {elapsed_min:.0f} min!")
        if self.__sla_breached:
            return f"[SLA BREACH] {self.__ticket_id} ({self.__priority})"
        return None

    def get_resolution_hours(self) -> float | None:
        if self.__closed_at:
            created = datetime.fromisoformat(self.__created_at)
            closed  = datetime.fromisoformat(self.__closed_at)
            return round((closed - created).total_seconds() / 3600, 2)
        return None

    def get_elapsed_hours(self) -> float:
        return round(
            (datetime.now() - datetime.fromisoformat(self.__created_at)).total_seconds() / 3600, 2
        )

    # Serialisation
    def to_dict(self) -> dict:
        return {
            "ticket_id":          self.__ticket_id,
            "employee_name":      self.__employee_name,
            "department":         self.__department,
            "issue_description":  self.__issue_description,
            "category":           self.__category,
            "priority":           self.__priority,
            "status":             self.__status,
            "created_at":         self.__created_at,
            "updated_at":         self.__updated_at,
            "closed_at":          self.__closed_at,
            "sla_breached":       self.__sla_breached,
            "ticket_type":        self.__ticket_type,
            "notes":              self.__notes,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserialise from dict without calling __init__."""
        obj = cls.__new__(cls)
        obj._Ticket__ticket_id         = data["ticket_id"]
        obj._Ticket__employee_name     = data["employee_name"]
        obj._Ticket__department        = data["department"]
        obj._Ticket__issue_description = data["issue_description"]
        obj._Ticket__category          = data["category"]
        obj._Ticket__priority          = data["priority"]
        obj._Ticket__status            = data["status"]
        obj._Ticket__created_at        = data["created_at"]
        obj._Ticket__updated_at        = data["updated_at"]
        obj._Ticket__closed_at         = data.get("closed_at")
        obj._Ticket__sla_breached      = data.get("sla_breached", False)
        obj._Ticket__ticket_type       = data.get("ticket_type", "General")
        obj._Ticket__notes             = data.get("notes", [])
        return obj

    # Static / Class Methods
    @staticmethod
    def generate_id() -> str:
        return f"TKT-{str(uuid.uuid4())[:8].upper()}"

    @classmethod
    def get_total_count(cls) -> int:
        return cls._ticket_counter

    @classmethod
    def from_user_input(cls, employee_name, department, issue_desc, category):
        """Factory class method."""
        return cls(employee_name, department, issue_desc, category)

    # Display
    def display(self):
        sla  = "SLA:BREACHED" if self.__sla_breached else "SLA:OK"
        res  = f"  Resolved In : {self.get_resolution_hours()} hrs" if self.__closed_at else ""
        print(f"""
-----------------------------------------------------------|
|  Ticket ID    : {self.__ticket_id:<41}|
|  Employee     : {self.__employee_name[:40]:<41}|
|  Department   : {self.__department[:40]:<41}|
|  Category     : {self.__category[:40]:<41}|
|  Priority     : {self.__priority:<41}|
|  Status       : {self.__status:<41}|
|  Type         : {self.__ticket_type:<41}|
|  SLA          : {sla:<41}|
|  Created At   : {self.__created_at[:19]:<41}|
|  Issue        : {self.__issue_description[:40]:<41}|
-----------------------------------------------------------|{res}""")



# SUBCLASSES (Inheritance + Polymorphism)


class IncidentTicket(Ticket):
    """Incident ticket with impact level. Demonstrates: inheritance, method overriding."""

    def __init__(self, employee_name, department, issue_description,
                 category, impact="Low"):
        super().__init__(employee_name, department, issue_description, category)
        self.__impact = impact
        self._set_type("Incident")

    @property
    def impact(self): return self.__impact

    def display(self):       # Method overriding (Polymorphism)
        super().display()
        print(f"  [Incident] Impact: {self.__impact}")

    def to_dict(self):
        d = super().to_dict()
        d["impact"] = self.__impact
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj._IncidentTicket__impact = data.get("impact", "Low")
        return obj


class ServiceRequest(Ticket):
    """Service request ticket. Demonstrates: inheritance, encapsulation."""

    def __init__(self, employee_name, department, issue_description,
                 category, requested_service="General"):
        super().__init__(employee_name, department, issue_description, category)
        self.__requested_service = requested_service
        self._set_type("ServiceRequest")

    @property
    def requested_service(self): return self.__requested_service

    def display(self):
        super().display()
        print(f"  [ServiceRequest] Service: {self.__requested_service}")

    def to_dict(self):
        d = super().to_dict()
        d["requested_service"] = self.__requested_service
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj._ServiceRequest__requested_service = data.get("requested_service", "General")
        return obj


class ProblemRecord(Ticket):
    """Problem record for recurring issues. Demonstrates: inheritance."""

    def __init__(self, employee_name, department, issue_description,
                 category, recurrence_count=5):
        super().__init__(employee_name, department, issue_description, category)
        self.__recurrence_count = recurrence_count
        self._set_type("ProblemRecord")

    @property
    def recurrence_count(self): return self.__recurrence_count

    def display(self):
        super().display()
        print(f"  [ProblemRecord] Recurrences: {self.__recurrence_count}")

    def to_dict(self):
        d = super().to_dict()
        d["recurrence_count"] = self.__recurrence_count
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj._ProblemRecord__recurrence_count = data.get("recurrence_count", 5)
        return obj


class ChangeRequest(Ticket):
    """Change request. Demonstrates: inheritance, polymorphism."""

    def __init__(self, employee_name, department, issue_description,
                 category, change_reason="Not specified"):
        super().__init__(employee_name, department, issue_description, category)
        self.__change_reason = change_reason
        self._set_type("ChangeRequest")

    @property
    def change_reason(self): return self.__change_reason

    def display(self):
        super().display()
        print(f"  [ChangeRequest] Reason: {self.__change_reason}")

    def to_dict(self):
        d = super().to_dict()
        d["change_reason"] = self.__change_reason
        return d

    @classmethod
    def from_dict(cls, data):
        obj = super().from_dict(data)
        obj._ChangeRequest__change_reason = data.get("change_reason", "Not specified")
        return obj


# TICKET ITERATOR (Advanced Python)

class TicketIterator:
    """
    Custom iterator over tickets.
    Demonstrates: __iter__, __next__, StopIteration.
    """
    def __init__(self, tickets: list):
        self._tickets = tickets
        self._index   = 0

    def __iter__(self):
        return self

    def __next__(self) -> Ticket:
        if self._index >= len(self._tickets):
            raise StopIteration
        t = self._tickets[self._index]
        self._index += 1
        return t


# TYPE MAP

TYPE_CLASS_MAP: dict = {
    "Incident":       IncidentTicket,
    "ServiceRequest": ServiceRequest,
    "ProblemRecord":  ProblemRecord,
    "ChangeRequest":  ChangeRequest,
    "General":        Ticket,
}


#  TICKET MANAGER

class TicketManager:
    """
    CRUD + persistence + SLA + ITIL problem detection.
    Demonstrates: encapsulation, class methods, generators, map/filter/reduce.
    """

    def __init__(self):
        self.__tickets: list[Ticket] = []
        self.__id_index: dict[str, Ticket] = {}   # dict for O(1) lookup
        self.__load_tickets()

    # Persistence
    def __load_tickets(self):
        """Load tickets from JSON. Demonstrates: file read, JSON, try/except/finally."""
        try:
            with open(TICKETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data:
                t_type = d.get("ticket_type", "General")
                cls    = TYPE_CLASS_MAP.get(t_type, Ticket)
                ticket = cls.from_dict(d)
                self.__tickets.append(ticket)
                tid = ticket.ticket_id.strip().upper()
                self.__id_index[tid] = ticket
            print(f"Loaded {len(self.__tickets)} tickets from storage.")
            log_event("INFO", f"Loaded {len(self.__tickets)} tickets from {TICKETS_FILE}")
        except FileNotFoundError:
            log_event("INFO", "tickets.json not found. Starting fresh.")
        except json.JSONDecodeError as e:
            log_event("ERROR", f"JSON decode error: {e}")
        except Exception as e:
            log_event("ERROR", f"Unexpected load error: {e}")
        finally:
            pass  # finally block always runs

    @log_call
    def save_tickets(self):
        """Persist tickets to JSON. Demonstrates: file write, JSON, context manager."""
        try:
            import os
            os.makedirs("data", exist_ok=True)
            with open(TICKETS_FILE, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.__tickets], f, indent=2)
        except IOError as e:
            log_event("ERROR", f"Failed to save tickets: {e}")
            raise

    # CRUD

    @log_ticket_event("CREATED")
    def create_ticket(self, employee_name: str, department: str,
                      issue_description: str, category: str,
                      ticket_type: str = "Incident", **kwargs) -> Ticket:
        try:
            if not issue_description.strip():
                raise EmptyFieldError("Issue description cannot be empty.")

            cls    = TYPE_CLASS_MAP.get(ticket_type, IncidentTicket)
            ticket = cls(employee_name, department, issue_description,
                         category, **kwargs)

            tid = ticket.ticket_id.upper()

            # Duplicate check
            if tid in self.__id_index:
                raise DuplicateTicketError(f"Duplicate ticket ID: {ticket.ticket_id}")

            self.__tickets.append(ticket)
            self.__id_index[tid] = ticket
            self.save_tickets()
            log_event("INFO",
                f"Ticket created: {ticket.ticket_id} | {ticket.priority} | {category}")
            return ticket

        except EmptyFieldError:
            log_event("ERROR", "Ticket creation failed: empty description")
            raise
        except Exception as e:
            log_event("ERROR", f"Ticket creation failed: {e}")
            raise

    def get_all_tickets(self) -> list[Ticket]:
        """Returns all tickets, refreshing SLA status."""
        for t in self.__tickets:
            if t.status != "Closed":
                t.check_sla()
        return list(self.__tickets)

    def search_by_id(self, ticket_id: str) -> Ticket | None:
        """O(1) lookup using dict index. Always normalizes to uppercase."""
        if not ticket_id:
            return None
        tid = ticket_id.strip().upper()
        return self._TicketManager__id_index.get(tid)

    def update_status(self, ticket_id: str, new_status: str) -> bool:
        ticket = self.search_by_id(ticket_id)
        if not ticket:
            log_event("WARNING", f"Update failed: ticket {ticket_id} not found")
            return False
        try:
            old = ticket.status
            ticket.status = new_status
            self.save_tickets()
            log_event("INFO",
                f"Ticket {ticket_id} updated: {old} -> {new_status}")
            return True
        except ValueError as e:
            log_event("ERROR", str(e))
            raise

    @log_ticket_event("CLOSED")
    def close_ticket(self, ticket_id: str) -> bool:
        result = self.update_status(ticket_id, "Closed")
        if result:
            log_event("INFO", f"Ticket {ticket_id} closed.")
        return result

    def delete_ticket(self, ticket_id: str) -> bool:
        tid = ticket_id.strip().upper()
        if tid not in self.__id_index:
            return False
        self.__tickets = [t for t in self.__tickets if t.ticket_id.upper() != tid]
        del self.__id_index[tid]
        self.save_tickets()
        log_event("INFO", f"Ticket {tid} deleted.")
        return True

    # Generator: yield pending tickets
    def pending_tickets_generator(self):
        """Generator – yields open/in-progress tickets one at a time."""
        for ticket in self.__tickets:
            if ticket.status in ("Open", "In Progress"):
                yield ticket

    # SLA & Escalation
    def check_all_sla(self) -> list[Ticket]:
        breached = [t for t in self.__tickets
                    if t.status != "Closed" and t.check_sla()]
        for t in breached:
            log_event("WARNING", f"SLA Breached: {t.ticket_id} ({t.priority})")
        self.save_tickets()
        return breached

    def check_all_escalations(self) -> list[str]:
        alerts = []
        for t in self.__tickets:
            msg = t.check_escalation()
            if msg:
                alerts.append(msg)
                log_event("WARNING", msg)
        return alerts

    # Problem Management (ITIL)
    def check_problem_records(self) -> list[ProblemRecord]:
        """
        If same category appears 5+ times in open tickets,
        auto-create a ProblemRecord.
        Uses: Counter, filter, list comprehension.
        """
        open_tickets = list(filter(
            lambda t: t.status != "Closed" and t.ticket_type not in
                      ("ProblemRecord", "ChangeRequest"),
            self.__tickets
        ))
        cat_counts = Counter(map(lambda t: t.category, open_tickets))

        existing_problem_cats: set = {
            t.category for t in self.__tickets
            if t.ticket_type == "ProblemRecord" and t.status != "Closed"
        }

        created: list[ProblemRecord] = []
        for cat, count in cat_counts.items():
            if count >= 5 and cat not in existing_problem_cats:
                pr = self.create_ticket(
                    "System (Auto)", "IT",
                    f"Recurring issue detected: {cat}",
                    cat, ticket_type="ProblemRecord",
                    recurrence_count=count
                )
                created.append(pr)
                log_event("WARNING",
                    f"Problem Record auto-created: {cat} ({count} occurrences)")
        return created

    # Advanced queries (map / filter / reduce)
    def get_open_tickets(self) -> list[Ticket]:
        return list(filter(lambda t: t.status == "Open", self.__tickets))

    def get_closed_tickets(self) -> list[Ticket]:
        return list(filter(lambda t: t.status == "Closed", self.__tickets))

    def get_tickets_by_priority(self, priority: str) -> list[Ticket]:
        return [t for t in self.__tickets if t.priority == priority]

    def get_tickets_by_status(self, status: str) -> list[Ticket]:
        return [t for t in self.__tickets if t.status == status]

    def get_tickets_by_dept(self, dept: str) -> list[Ticket]:
        return [t for t in self.__tickets if t.department.lower() == dept.lower()]

    def get_sorted_by_priority(self) -> list[Ticket]:
        order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
        return sorted(self.__tickets, key=lambda t: order.get(t.priority, 9))

    def count_by_priority(self) -> dict:
        """reduce() to count tickets per priority."""
        return reduce(
            lambda acc, t: {**acc, t.priority: acc.get(t.priority, 0) + 1},
            self.__tickets, {}
        )

    def get_all_ids(self) -> list[str]:
        """map() to extract IDs."""
        return list(map(lambda t: t.ticket_id, self.__tickets))

    def get_unique_categories(self) -> set:
        """Set comprehension for unique categories."""
        return {t.category for t in self.__tickets}

    # Special method: len support
    def __len__(self):
        return len(self.__tickets)

    def __iter__(self):
        """Make TicketManager iterable."""
        return TicketIterator(self.__tickets)

    def __contains__(self, ticket_id: str) -> bool:
        return ticket_id.strip().upper() in self.__id_index