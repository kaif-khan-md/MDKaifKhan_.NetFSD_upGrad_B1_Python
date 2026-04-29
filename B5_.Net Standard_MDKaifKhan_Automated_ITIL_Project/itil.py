"""
itil.py - ITIL Workflow Engine
Implements:
  - Incident Management
  - Service Request Management
  - Problem Management (auto-detect recurring issues)
  - Change Management
  - SLA Monitoring
Uses: OOP, inheritance, polymorphism, encapsulation, iterators, generators,
      JSON file handling, custom exceptions, decorators.
"""

import json
import os
import re
from datetime import datetime
from collections import Counter
from functools import reduce

from logger import Logger, log_event, log_call, DuplicateTicketError, SLABreachError

DATA_DIR      = "data"
PROBLEMS_FILE = os.path.join(DATA_DIR, "problems.json")
os.makedirs(DATA_DIR, exist_ok=True)

logger = Logger()


#  Priority / SLA constants 

PRIORITY_SLA: tuple = (
    ("P1", 1),
    ("P2", 4),
    ("P3", 8),
    ("P4", 24),
)
SLA_MAP: dict = dict(PRIORITY_SLA)

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

# Categories as a set
INCIDENT_CATEGORIES: set = {
    "Server Down", "Internet Down", "High CPU Usage",
    "Application Crash", "Disk Space Full"
}
SERVICE_CATEGORIES: set = {
    "Password Reset", "Software Install", "Laptop Slow",
    "Printer Issue", "Outlook Issue", "Other"
}



#  Iterator: Ticket Iterator

class TicketIterator:
    """
    Custom iterator over a list of tickets.
    Demonstrates: __iter__, __next__, StopIteration.
    """
    def __init__(self, tickets: list):
        self.__tickets = tickets
        self.__index   = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index >= len(self.__tickets):
            raise StopIteration
        ticket = self.__tickets[self.__index]
        self.__index += 1
        return ticket


# Base ITIL Record

class ITILRecord:
    """Base class for all ITIL records. Demonstrates encapsulation + special methods."""

    def __init__(self, record_id: str, title: str, category: str,
                 description: str, priority: str, created_by: str):
        self._record_id  = record_id
        self._title      = title
        self._category   = category
        self._description = description
        self._priority   = priority
        self._status     = "Open"
        self._created_by = created_by
        self._created_at = datetime.now().isoformat()
        self._updated_at = self._created_at
        self._notes: list[str] = []

    # Special methods
    def __str__(self):
        return f"[{self._record_id}] {self._priority} | {self._title} | {self._status}"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._record_id}, priority={self._priority})"

    def __eq__(self, other):
        if isinstance(other, ITILRecord):
            return self._record_id == other._record_id
        return False

    def __hash__(self):
        return hash(self._record_id)

    # Properties 
    @property
    def record_id(self):   return self._record_id
    @property
    def title(self):       return self._title
    @property
    def category(self):    return self._category
    @property
    def priority(self):    return self._priority
    @property
    def status(self):      return self._status
    @property
    def created_at(self):  return self._created_at
    @property
    def notes(self):       return list(self._notes)

    @status.setter
    def status(self, val: str):
        allowed = {"Open", "In Progress", "Resolved", "Closed", "Pending"}
        if val not in allowed:
            raise ValueError(f"Invalid status '{val}'. Allowed: {allowed}")
        self._status     = val
        self._updated_at = datetime.now().isoformat()

    def add_note(self, note: str):
        self._notes.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {note}")

    def check_sla_hours(self) -> float:
        """Return elapsed hours since creation."""
        created = datetime.fromisoformat(self._created_at)
        return (datetime.now() - created).total_seconds() / 3600

    def is_sla_breached(self) -> bool:
        limit = SLA_MAP.get(self._priority, 24)
        return self.check_sla_hours() > limit and self._status not in ("Resolved", "Closed")

    def to_dict(self) -> dict:
        return {
            "record_id":   self._record_id,
            "title":       self._title,
            "category":    self._category,
            "description": self._description,
            "priority":    self._priority,
            "status":      self._status,
            "created_by":  self._created_by,
            "created_at":  self._created_at,
            "updated_at":  self._updated_at,
            "notes":       self._notes,
            "type":        self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls.__new__(cls)
        obj._record_id   = data["record_id"]
        obj._title       = data["title"]
        obj._category    = data["category"]
        obj._description = data["description"]
        obj._priority    = data["priority"]
        obj._status      = data["status"]
        obj._created_by  = data["created_by"]
        obj._created_at  = data["created_at"]
        obj._updated_at  = data.get("updated_at", data["created_at"])
        obj._notes       = data.get("notes", [])
        return obj



#  Incident Management

class Incident(ITILRecord):
    """
    ITIL Incident: unplanned interruption or quality reduction.
    Demonstrates: inheritance, polymorphism (overrides display/to_dict).
    """

    def __init__(self, record_id, title, category, description,
                 priority, created_by, impact="Medium", urgency="Medium"):
        super().__init__(record_id, title, category, description, priority, created_by)
        self.__impact  = impact
        self.__urgency = urgency
        self.__resolved_at = None

    @property
    def impact(self):  return self.__impact
    @property
    def urgency(self): return self.__urgency

    def resolve(self, resolution_note: str = ""):
        self.status = "Resolved"
        self.__resolved_at = datetime.now().isoformat()
        if resolution_note:
            self.add_note(f"Resolution: {resolution_note}")
        log_event("INFO", f"Incident resolved: {self._record_id}")

    def get_resolution_time(self) -> float | None:
        if self.__resolved_at:
            created  = datetime.fromisoformat(self._created_at)
            resolved = datetime.fromisoformat(self.__resolved_at)
            return round((resolved - created).total_seconds() / 3600, 2)
        return None

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"impact": self.__impact, "urgency": self.__urgency,
                  "resolved_at": self.__resolved_at})
        return d

    @classmethod
    def from_dict(cls, data: dict):
        obj = super().from_dict(data)
        obj._Incident__impact      = data.get("impact", "Medium")
        obj._Incident__urgency     = data.get("urgency", "Medium")
        obj._Incident__resolved_at = data.get("resolved_at")
        return obj

    def display(self):
        """Polymorphic display – overrides base."""
        print(f"""
  ┌── INCIDENT ─────────────────────────────────────┐
  │  ID       : {self._record_id}
  │  Title    : {self._title}
  │  Category : {self._category}
  │  Priority : {self._priority}  Impact: {self.__impact}  Urgency: {self.__urgency}
  │  Status   : {self._status}
  │  SLA      : {"BREACHED" if self.is_sla_breached() else "OK"}
  │  Created  : {self._created_at[:19]}
  └─────────────────────────────────────────────────┘""")


#  Service Request Management
class ServiceRequest(ITILRecord):
    """
    ITIL Service Request: standard change or pre-approved request.
    """

    def __init__(self, record_id, title, category, description,
                 priority, created_by, service_type="General", approver="IT Manager"):
        super().__init__(record_id, title, category, description, priority, created_by)
        self.__service_type = service_type
        self.__approver     = approver
        self.__approved     = False

    @property
    def service_type(self): return self.__service_type
    @property
    def approver(self):     return self.__approver
    @property
    def approved(self):     return self.__approved

    def approve(self):
        self.__approved = True
        self.status = "In Progress"
        self.add_note(f"Approved by {self.__approver}")
        log_event("INFO", f"Service Request approved: {self._record_id}")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({"service_type": self.__service_type,
                  "approver": self.__approver, "approved": self.__approved})
        return d

    @classmethod
    def from_dict(cls, data: dict):
        obj = super().from_dict(data)
        obj._ServiceRequest__service_type = data.get("service_type", "General")
        obj._ServiceRequest__approver     = data.get("approver", "IT Manager")
        obj._ServiceRequest__approved     = data.get("approved", False)
        return obj

    def display(self):
        status_ap = "Approved" if self.__approved else "⏳ Pending Approval"
        print(f"""
  ┌── SERVICE REQUEST ───────────────────────────────┐
  │  ID           : {self._record_id}
  │  Title        : {self._title}
  │  Service Type : {self.__service_type}
  │  Approver     : {self.__approver}  {status_ap}
  │  Priority     : {self._priority}
  │  Status       : {self._status}
  │  Created      : {self._created_at[:19]}
  └──────────────────────────────────────────────────┘""")



# Problem Management

class ProblemRecord(ITILRecord):
    """
    ITIL Problem: root cause of one or more incidents.
    Auto-created when same issue category recurs 5+ times.
    """

    def __init__(self, record_id, title, category, description,
                 priority, created_by, recurrence_count=5, root_cause="Under investigation"):
        super().__init__(record_id, title, category, description, priority, created_by)
        self.__recurrence_count = recurrence_count
        self.__root_cause       = root_cause
        self.__workaround: str | None = None
        self.__known_error      = False

    @property
    def recurrence_count(self): return self.__recurrence_count
    @property
    def root_cause(self):       return self.__root_cause
    @property
    def known_error(self):      return self.__known_error

    def set_root_cause(self, cause: str):
        self.__root_cause = cause
        self.add_note(f"Root cause identified: {cause}")

    def set_workaround(self, workaround: str):
        self.__workaround   = workaround
        self.__known_error  = True
        self.add_note(f"Workaround: {workaround}")
        log_event("INFO", f"Problem workaround set: {self._record_id}")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "recurrence_count": self.__recurrence_count,
            "root_cause":       self.__root_cause,
            "workaround":       self.__workaround,
            "known_error":      self.__known_error,
        })
        return d

    @classmethod
    def from_dict(cls, data: dict):
        obj = super().from_dict(data)
        obj._ProblemRecord__recurrence_count = data.get("recurrence_count", 5)
        obj._ProblemRecord__root_cause       = data.get("root_cause", "Under investigation")
        obj._ProblemRecord__workaround       = data.get("workaround")
        obj._ProblemRecord__known_error      = data.get("known_error", False)
        return obj

    def display(self):
        print(f"""
  ┌── PROBLEM RECORD ────────────────────────────────┐
  │  ID           : {self._record_id}
  │  Category     : {self._category}
  │  Recurrences  : {self.__recurrence_count}
  │  Root Cause   : {self.__root_cause}
  │  Known Error  : {"Yes" if self.__known_error else "No"}
  │  Status       : {self._status}
  │  Created      : {self._created_at[:19]}
  └──────────────────────────────────────────────────┘""")


# Change Management

class ChangeRequest(ITILRecord):
    """
    ITIL Change Request: controlled change to IT infrastructure.
    """
    CHANGE_TYPES = ("Standard", "Normal", "Emergency")

    def __init__(self, record_id, title, category, description,
                 priority, created_by, change_type="Normal",
                 change_reason="Not specified", cab_required=False):
        super().__init__(record_id, title, category, description, priority, created_by)
        if change_type not in self.CHANGE_TYPES:
            raise ValueError(f"change_type must be one of {self.CHANGE_TYPES}")
        self.__change_type   = change_type
        self.__change_reason = change_reason
        self.__cab_required  = cab_required
        self.__cab_approved  = False
        self.__implementation_date: str | None = None

    @property
    def change_type(self):   return self.__change_type
    @property
    def cab_required(self):  return self.__cab_required
    @property
    def cab_approved(self):  return self.__cab_approved

    def approve_cab(self):
        self.__cab_approved = True
        self.add_note("CAB approval granted")
        log_event("INFO", f"CAB approved change: {self._record_id}")

    def schedule_implementation(self, date_str: str):
        self.__implementation_date = date_str
        self.add_note(f"Implementation scheduled: {date_str}")

    def to_dict(self) -> dict:
        d = super().to_dict()
        d.update({
            "change_type":          self.__change_type,
            "change_reason":        self.__change_reason,
            "cab_required":         self.__cab_required,
            "cab_approved":         self.__cab_approved,
            "implementation_date":  self.__implementation_date,
        })
        return d

    @classmethod
    def from_dict(cls, data: dict):
        obj = super().from_dict(data)
        obj._ChangeRequest__change_type          = data.get("change_type", "Normal")
        obj._ChangeRequest__change_reason        = data.get("change_reason", "")
        obj._ChangeRequest__cab_required         = data.get("cab_required", False)
        obj._ChangeRequest__cab_approved         = data.get("cab_approved", False)
        obj._ChangeRequest__implementation_date  = data.get("implementation_date")
        return obj

    def display(self):
        cab = "Required" if self.__cab_required else "Not Required"
        cab_ap = "Approved" if self.__cab_approved else ""
        print(f"""
  ┌── CHANGE REQUEST ────────────────────────────────┐
  │  ID          : {self._record_id}
  │  Title       : {self._title}
  │  Type        : {self.__change_type}
  │  CAB         : {cab}{cab_ap}
  │  Reason      : {self.__change_reason}
  │  Status      : {self._status}
  │  Created     : {self._created_at[:19]}
  └──────────────────────────────────────────────────┘""")



#  ITIL Manager – orchestrates all workflows

RECORD_CLASS_MAP = {
    "Incident":       Incident,
    "ServiceRequest": ServiceRequest,
    "ProblemRecord":  ProblemRecord,
    "ChangeRequest":  ChangeRequest,
}


class ITILManager:
    """
    Manages all ITIL records: incidents, service requests,
    problem records, and change requests.
    Persists problem records to problems.json.
    """

    def __init__(self):
        self.__records: list[ITILRecord] = []
        self.__id_set: set[str] = set()   # demonstrates set usage
        self.__load()

    # Persistence 

    def __load(self):
        try:
            with open(PROBLEMS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data:
                cls = RECORD_CLASS_MAP.get(d.get("type", "Incident"), Incident)
                rec = cls.from_dict(d)
                self.__records.append(rec)
                self.__id_set.add(rec.record_id)
            log_event("INFO", f"Loaded {len(self.__records)} ITIL records from {PROBLEMS_FILE}")
        except FileNotFoundError:
            log_event("INFO", f"{PROBLEMS_FILE} not found. Starting fresh.")
        except json.JSONDecodeError as e:
            log_event("ERROR", f"JSON decode error in {PROBLEMS_FILE}: {e}")

    @log_call
    def save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(PROBLEMS_FILE, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in self.__records], f, indent=2)
        except IOError as e:
            log_event("ERROR", f"Failed to save ITIL records: {e}")

    # Factory: create any record type 

    def _generate_id(self, prefix: str) -> str:
        import uuid
        return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"

    def create_incident(self, title, category, description, created_by,
                        impact="Medium", urgency="Medium") -> Incident:
        priority = PRIORITY_MAP.get(category, "P4")
        rid = self._generate_id("INC")
        if rid in self.__id_set:
            raise DuplicateTicketError(f"Duplicate ID generated: {rid}")
        inc = Incident(rid, title, category, description, priority, created_by,
                       impact, urgency)
        self.__records.append(inc)
        self.__id_set.add(rid)
        self.save()
        log_event("INFO", f"Incident created: {rid} | {priority} | {category}")
        return inc

    def create_service_request(self, title, category, description, created_by,
                                service_type="General", approver="IT Manager") -> ServiceRequest:
        priority = PRIORITY_MAP.get(category, "P4")
        rid = self._generate_id("SRQ")
        sr = ServiceRequest(rid, title, category, description, priority,
                            created_by, service_type, approver)
        self.__records.append(sr)
        self.__id_set.add(rid)
        self.save()
        log_event("INFO", f"Service Request created: {rid} | {category}")
        return sr

    def create_problem_record(self, category: str, recurrence_count: int,
                               created_by: str = "System (Auto)") -> ProblemRecord:
        priority = PRIORITY_MAP.get(category, "P3")
        rid = self._generate_id("PRB")
        pr = ProblemRecord(
            rid,
            f"Recurring Issue: {category}",
            category,
            f"Same issue '{category}' has occurred {recurrence_count} times.",
            priority, created_by, recurrence_count
        )
        self.__records.append(pr)
        self.__id_set.add(rid)
        self.save()
        log_event("WARNING", f"Problem Record created: {rid} | {category} | {recurrence_count}x")
        return pr

    def create_change_request(self, title, category, description, created_by,
                               change_type="Normal", change_reason="",
                               cab_required=False) -> ChangeRequest:
        priority = PRIORITY_MAP.get(category, "P4")
        rid = self._generate_id("CHG")
        cr = ChangeRequest(rid, title, category, description, priority,
                           created_by, change_type, change_reason, cab_required)
        self.__records.append(cr)
        self.__id_set.add(rid)
        self.save()
        log_event("INFO", f"Change Request created: {rid} | {change_type} | {category}")
        return cr

    # Queries

    def get_all(self) -> list[ITILRecord]:
        return list(self.__records)

    def get_by_type(self, rtype: str) -> list[ITILRecord]:
        return [r for r in self.__records if r.__class__.__name__ == rtype]

    def get_by_id(self, rid: str) -> ITILRecord | None:
        for r in self.__records:
            if r.record_id == rid.strip().upper():
                return r
        return None

    # Generator: yield SLA-breached records 
    def sla_breach_generator(self):
        """Generator that yields breached ITIL records."""
        for record in self.__records:
            if record.is_sla_breached():
                yield record

    # Problem Detection 
    def detect_problems_from_tickets(self, ticket_manager) -> list[ProblemRecord]:
        """
        Scan ticket_manager for categories with 5+ open tickets.
        Auto-create ProblemRecord for each.
        Uses: Counter, list comprehension, filter.
        """
        all_tickets = ticket_manager.get_all_tickets()
        open_tickets = list(filter(
            lambda t: t.status != "Closed" and t.ticket_type not in ("ProblemRecord", "ChangeRequest"),
            all_tickets
        ))
        category_counts = Counter(map(lambda t: t.category, open_tickets))

        # Categories that already have an open problem record
        existing_problem_cats: set = {
            r.category for r in self.__records
            if isinstance(r, ProblemRecord) and r.status not in ("Resolved", "Closed")
        }

        created: list[ProblemRecord] = []
        for cat, count in category_counts.items():
            if count >= 5 and cat not in existing_problem_cats:
                pr = self.create_problem_record(cat, count)
                created.append(pr)

        return created

    # SLA Monitoring 
    def check_sla_all(self) -> list[ITILRecord]:
        breached = list(self.sla_breach_generator())
        for r in breached:
            log_event("WARNING", f"SLA Breached: {r.record_id} ({r.priority}) | {r.category}")
        return breached

    # Escalation warnings 
    def escalation_warnings(self) -> list[str]:
        warnings = []
        for r in self.__records:
            if r.status in ("Resolved", "Closed"):
                continue
            elapsed_min = r.check_sla_hours() * 60
            if r.priority == "P1" and elapsed_min > 30:
                warnings.append(f"P1 ESCALATION: {r.record_id} open {elapsed_min:.0f} min!")
            elif r.priority == "P2" and elapsed_min > 120:
                warnings.append(f"P2 ESCALATION: {r.record_id} open {elapsed_min:.0f} min!")
            if r.is_sla_breached():
                warnings.append(f"SLA BREACH: {r.record_id} ({r.priority}) | {r.category}")
        return warnings

    # Stats via map/filter/reduce 
    def summary_stats(self) -> dict:
        records = self.__records
        total   = len(records)
        open_r  = len(list(filter(lambda r: r.status == "Open", records)))
        p1_r    = len(list(filter(lambda r: r.priority == "P1", records)))
        breached= len(list(filter(lambda r: r.is_sla_breached(), records)))

        type_counts = reduce(
            lambda acc, r: {**acc, r.__class__.__name__: acc.get(r.__class__.__name__, 0) + 1},
            records, {}
        )

        return {
            "total": total, "open": open_r, "p1": p1_r,
            "breached": breached, "by_type": type_counts
        }

    # Display helpers
    def display_all(self, rtype: str | None = None):
        records = self.get_by_type(rtype) if rtype else self.__records
        if not records:
            print("  No ITIL records found.")
            return
        iterator = TicketIterator(records)
        for rec in iterator:
            print(f"  {rec}")

    def display_sla_report(self):
        breached = self.check_sla_all()
        warnings = self.escalation_warnings()
        print(f"\n  SLA BREACHED: {len(breached)}")
        for r in breached:
            print(f"  {r.record_id} | {r.priority} | {r.category}")
        print(f"\n  ESCALATION WARNINGS: {len(warnings)}")
        for w in warnings:
            print(f"    {w}")