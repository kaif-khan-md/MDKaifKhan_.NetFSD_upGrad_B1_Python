"""
tests.py - Test Suite for Smart IT Service Desk
Tests: ticket creation, priority logic, SLA breach, auto-monitoring tickets,
       file read/write, search, exception handling, ITIL workflows,
       advanced Python features (iterators, generators, map/filter/reduce).
Run: python tests.py

"""

import os
import sys
import json
import time
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Set working dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from utils import (
    PRIORITY_MAP, SLA_HOURS, validate_ticket_id, validate_email,
    validate_date, filter_open_tickets, map_to_ids, count_by_priority,
    priority_label_generator, backup_tickets_to_csv
)
from logger import (
    Logger, log_event, DuplicateTicketError,
    InvalidTicketIDError, EmptyFieldError, SLABreachError, LogLevelError
)
from tickets import (
    Ticket, IncidentTicket, ServiceRequest, ProblemRecord,
    ChangeRequest, TicketManager, TicketIterator
)
from monitor import Monitor, THRESHOLDS
from reports import ReportGenerator
from itil import (
    ITILManager, Incident, ServiceRequest as SR,
    ProblemRecord as PR, ChangeRequest as CR
)

#  Helpers

def make_manager(tmpdir: str) -> TicketManager:
    """Create a TicketManager backed by a temp directory."""
    import utils
    original = utils.TICKETS_FILE
    utils.TICKETS_FILE = os.path.join(tmpdir, "tickets.json")
    import tickets as tm_mod
    original_tf = tm_mod.TICKETS_FILE
    tm_mod.TICKETS_FILE = utils.TICKETS_FILE
    mgr = TicketManager()
    # restore
    utils.TICKETS_FILE = original
    tm_mod.TICKETS_FILE = original_tf
    return mgr


# TICKET CREATION

class TestTicketCreation(unittest.TestCase):

    def setUp(self):
        self.t1 = Ticket("Alice", "IT", "Server is down", "Server Down")
        self.t2 = IncidentTicket("Bob", "HR", "Outlook not opening", "Outlook Issue", impact="High")
        self.t3 = ServiceRequest("Carol", "Finance", "Password reset needed", "Password Reset",
                                 requested_service="Account Management")
        self.t4 = ProblemRecord("System", "IT", "Recurring printer issue", "Printer Issue",
                                recurrence_count=6)
        self.t5 = ChangeRequest("Dave", "Ops", "Patch deployment", "Other",
                                change_reason="Security patch")

    def test_ticket_id_format(self):
        self.assertTrue(self.t1.ticket_id.startswith("TKT-"))
        self.assertEqual(len(self.t1.ticket_id), 12)   # TKT- + 8 chars

    def test_unique_ids(self):
        ids = {self.t1.ticket_id, self.t2.ticket_id, self.t3.ticket_id,
               self.t4.ticket_id, self.t5.ticket_id}
        self.assertEqual(len(ids), 5)

    def test_fields_stored(self):
        self.assertEqual(self.t1.employee_name, "Alice")
        self.assertEqual(self.t1.department, "IT")
        self.assertEqual(self.t1.issue_description, "Server is down")
        self.assertEqual(self.t1.category, "Server Down")
        self.assertEqual(self.t1.status, "Open")

    def test_initial_status_open(self):
        for t in [self.t1, self.t2, self.t3, self.t4, self.t5]:
            self.assertEqual(t.status, "Open")

    def test_created_at_is_today(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertTrue(self.t1.created_at.startswith(today))

    def test_incident_ticket_type(self):
        self.assertEqual(self.t2.ticket_type, "Incident")
        self.assertEqual(self.t2.impact, "High")

    def test_service_request_type(self):
        self.assertEqual(self.t3.ticket_type, "ServiceRequest")
        self.assertEqual(self.t3.requested_service, "Account Management")

    def test_problem_record_type(self):
        self.assertEqual(self.t4.ticket_type, "ProblemRecord")
        self.assertEqual(self.t4.recurrence_count, 6)

    def test_change_request_type(self):
        self.assertEqual(self.t5.ticket_type, "ChangeRequest")
        self.assertEqual(self.t5.change_reason, "Security patch")

    def test_serialisation_roundtrip(self):
        d  = self.t1.to_dict()
        t2 = Ticket.from_dict(d)
        self.assertEqual(t2.ticket_id, self.t1.ticket_id)
        self.assertEqual(t2.priority,  self.t1.priority)
        self.assertEqual(t2.status,    self.t1.status)

    def test_special_methods(self):
        # __str__ and __repr__
        self.assertIn("TKT-", str(self.t1))
        self.assertIn("Ticket(", repr(self.t1))
        # __eq__
        self.assertEqual(self.t1, self.t1)
        self.assertNotEqual(self.t1, self.t2)
        # __len__ (notes count)
        self.assertEqual(len(self.t1), 0)
        self.t1.add_note("test note")
        self.assertEqual(len(self.t1), 1)

# PRIORITY LOGIC

class TestPriorityLogic(unittest.TestCase):

    def test_p1_categories(self):
        for cat in ["Server Down", "High CPU Usage"]:
            t = Ticket("X", "IT", "desc", cat)
            self.assertEqual(t.priority, "P1", f"Failed for: {cat}")

    def test_p2_categories(self):
        for cat in ["Internet Down", "Disk Space Full", "Application Crash"]:
            t = Ticket("X", "IT", "desc", cat)
            self.assertEqual(t.priority, "P2", f"Failed for: {cat}")

    def test_p3_categories(self):
        for cat in ["Laptop Slow", "Printer Issue", "Outlook Issue"]:
            t = Ticket("X", "IT", "desc", cat)
            self.assertEqual(t.priority, "P3", f"Failed for: {cat}")

    def test_p4_categories(self):
        for cat in ["Password Reset", "Software Install", "Other"]:
            t = Ticket("X", "IT", "desc", cat)
            self.assertEqual(t.priority, "P4", f"Failed for: {cat}")

    def test_unknown_category_defaults_p4(self):
        t = Ticket("X", "IT", "desc", "Unknown Category XYZ")
        self.assertEqual(t.priority, "P4")

    def test_priority_map_completeness(self):
        for cat, prio in PRIORITY_MAP.items():
            self.assertIn(prio, ("P1","P2","P3","P4"))

    def test_sla_hours_mapping(self):
        self.assertEqual(SLA_HOURS["P1"], 1)
        self.assertEqual(SLA_HOURS["P2"], 4)
        self.assertEqual(SLA_HOURS["P3"], 8)
        self.assertEqual(SLA_HOURS["P4"], 24)

# SLA BREACH

class TestSLABreach(unittest.TestCase):

    def test_fresh_ticket_not_breached(self):
        t = IncidentTicket("X", "IT", "fresh", "Server Down")
        self.assertFalse(t.check_sla())

    def test_sla_breach_by_backdating(self):
        """Simulate SLA breach by backdating created_at."""
        t = IncidentTicket("X", "IT", "old server", "Server Down")  # P1 = 1hr SLA
        # Backdate 2 hours
        past = (datetime.now() - timedelta(hours=2)).isoformat()
        t._Ticket__created_at = past
        self.assertTrue(t.check_sla())
        self.assertTrue(t.sla_breached)

    def test_p4_sla_not_breached_at_23hrs(self):
        t = Ticket("X", "IT", "password", "Password Reset")  # P4 = 24hr SLA
        past = (datetime.now() - timedelta(hours=23)).isoformat()
        t._Ticket__created_at = past
        self.assertFalse(t.check_sla())

    def test_p4_sla_breached_at_25hrs(self):
        t = Ticket("X", "IT", "password", "Password Reset")
        past = (datetime.now() - timedelta(hours=25)).isoformat()
        t._Ticket__created_at = past
        self.assertTrue(t.check_sla())

    def test_closed_ticket_not_breached(self):
        t = IncidentTicket("X", "IT", "old", "Server Down")
        past = (datetime.now() - timedelta(hours=5)).isoformat()
        t._Ticket__created_at = past
        t.status = "Closed"
        self.assertFalse(t.check_sla())

    def test_escalation_p1_after_30min(self):
        t = IncidentTicket("X", "IT", "server", "Server Down")
        past = (datetime.now() - timedelta(minutes=35)).isoformat()
        t._Ticket__created_at = past
        msg = t.check_escalation()
        self.assertIsNotNone(msg)
        self.assertIn("ESCALATION", msg)

    def test_no_escalation_fresh_ticket(self):
        t = IncidentTicket("X", "IT", "server", "Server Down")
        self.assertIsNone(t.check_escalation())

# AUTO MONITORING TICKET CREATION

class TestAutoMonitoring(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tm = TicketManager()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_high_cpu_creates_ticket(self):
        mon = Monitor()
        stats = {
            "cpu_percent": 95.0,       # exceeds 90%
            "ram_percent": 50.0,
            "disk_free_percent": 50.0,
        }
        alerts  = mon.check_thresholds(stats)
        self.assertTrue(any(a["metric"] == "cpu_percent" for a in alerts))
        created = mon.auto_create_tickets(alerts, self.tm)
        self.assertGreater(len(created), 0)
        self.assertEqual(created[0].priority, "P1")

    def test_high_ram_creates_ticket(self):
        mon    = Monitor()
        stats  = {"cpu_percent": 10.0, "ram_percent": 96.0, "disk_free_percent": 50.0}
        alerts = mon.check_thresholds(stats)
        self.assertTrue(any(a["metric"] == "ram_percent" for a in alerts))

    def test_low_disk_creates_ticket(self):
        mon    = Monitor()
        stats  = {"cpu_percent": 10.0, "ram_percent": 10.0, "disk_free_percent": 5.0}
        alerts = mon.check_thresholds(stats)
        self.assertTrue(any(a["metric"] == "disk_free_percent" for a in alerts))

    def test_normal_stats_no_alerts(self):
        mon    = Monitor()
        stats  = {"cpu_percent": 50.0, "ram_percent": 60.0, "disk_free_percent": 40.0}
        alerts = mon.check_thresholds(stats)
        self.assertEqual(len(alerts), 0)

    def test_alert_generator_yields_correctly(self):
        mon   = Monitor()
        stats = {"cpu_percent": 95.0, "ram_percent": 50.0, "disk_free_percent": 50.0}
        alerts = list(mon.alert_generator(stats))
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["metric"], "cpu_percent")

# FILE READ / WRITE

class TestFileHandling(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.tmpdir, "test_tickets.json")
        self.csv_path  = os.path.join(self.tmpdir, "test_backup.csv")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_ticket_to_dict_and_back(self):
        t = IncidentTicket("Alice", "IT", "Server crash", "Server Down", impact="High")
        d = t.to_dict()
        self.assertEqual(d["employee_name"], "Alice")
        self.assertEqual(d["priority"], "P1")
        self.assertEqual(d["ticket_type"], "Incident")
        self.assertEqual(d["impact"], "High")

    def test_json_write_and_read(self):
        tickets = [
            IncidentTicket("Alice", "IT", "Server crash", "Server Down").to_dict(),
            ServiceRequest("Bob", "HR", "Password reset", "Password Reset").to_dict(),
        ]
        with open(self.json_path, "w") as f:
            json.dump(tickets, f, indent=2)

        with open(self.json_path, "r") as f:
            loaded = json.load(f)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["employee_name"], "Alice")
        self.assertEqual(loaded[1]["ticket_type"], "ServiceRequest")

    def test_from_dict_preserves_all_fields(self):
        original = IncidentTicket("Carol", "Finance", "CPU high", "High CPU Usage",
                                  impact="High")
        d = original.to_dict()
        restored = IncidentTicket.from_dict(d)
        self.assertEqual(restored.ticket_id,      original.ticket_id)
        self.assertEqual(restored.priority,        original.priority)
        self.assertEqual(restored.employee_name,   original.employee_name)
        self.assertEqual(restored.ticket_type,     "Incident")

    def test_file_not_found_handled(self):
        """TicketManager should handle missing file gracefully."""
        import tickets as tm_mod
        orig = tm_mod.TICKETS_FILE
        tm_mod.TICKETS_FILE = "/nonexistent/path/tickets.json"
        try:
            mgr = TicketManager()   # should not raise
        except Exception as e:
            self.fail(f"TicketManager raised unexpectedly: {e}")
        finally:
            tm_mod.TICKETS_FILE = orig

# SEARCH TICKET

class TestSearchTicket(unittest.TestCase):

    def setUp(self):
        self.tm = TicketManager()
        self.t1 = self.tm.create_ticket("Alice", "IT", "Server crash", "Server Down",
                                         "Incident", impact="High")
        self.t2 = self.tm.create_ticket("Bob", "HR", "Password reset", "Password Reset",
                                         "ServiceRequest", requested_service="Account")

    def test_search_existing_ticket(self):
        found = self.tm.search_by_id(self.t1.ticket_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.ticket_id, self.t1.ticket_id)

    def test_search_case_insensitive(self):
        lower_id = self.t1.ticket_id.lower()
        found = self.tm.search_by_id(lower_id)
        self.assertIsNotNone(found)

    def test_search_nonexistent_returns_none(self):
        result = self.tm.search_by_id("TKT-XXXXXXXX")
        self.assertIsNone(result)

    def test_search_empty_returns_none(self):
        result = self.tm.search_by_id("   ")
        self.assertIsNone(result)

    def test_contains_operator(self):
        self.assertIn(self.t1.ticket_id, self.tm)
        self.assertNotIn("TKT-XXXXXXXX", self.tm)

    def test_get_by_priority(self):
        p1_tickets = self.tm.get_tickets_by_priority("P1")
        self.assertTrue(any(t.ticket_id == self.t1.ticket_id for t in p1_tickets))

    def test_get_by_status(self):
        open_tickets = self.tm.get_tickets_by_status("Open")
        self.assertTrue(len(open_tickets) >= 2)

    def test_get_sorted_by_priority(self):
        sorted_tickets = self.tm.get_sorted_by_priority()
        priorities = [t.priority for t in sorted_tickets]
        order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
        for i in range(len(priorities) - 1):
            self.assertLessEqual(order[priorities[i]], order[priorities[i+1]])


# EXCEPTION HANDLING

class TestExceptionHandling(unittest.TestCase):

    def setUp(self):
        self.tm = TicketManager()

    def test_empty_description_raises(self):
        with self.assertRaises(EmptyFieldError):
            Ticket("Alice", "IT", "   ", "Server Down")

    def test_empty_name_raises(self):
        with self.assertRaises(EmptyFieldError):
            Ticket("", "IT", "some issue", "Server Down")

    def test_invalid_status_raises(self):
        t = IncidentTicket("X", "IT", "desc", "Server Down")
        with self.assertRaises(ValueError):
            t.status = "INVALID_STATUS"

    def test_update_nonexistent_ticket(self):
        result = self.tm.update_status("TKT-XXXXXXXX", "Closed")
        self.assertFalse(result)

    def test_delete_nonexistent_ticket(self):
        result = self.tm.delete_ticket("TKT-XXXXXXXX")
        self.assertFalse(result)

    def test_custom_exceptions_hierarchy(self):
        self.assertIsInstance(EmptyFieldError(), Exception)
        self.assertIsInstance(DuplicateTicketError(), Exception)
        self.assertIsInstance(InvalidTicketIDError(), Exception)
        self.assertIsInstance(SLABreachError(), Exception)

    def test_logger_invalid_level_raises(self):
        logger = Logger()
        with self.assertRaises(LogLevelError):
            logger._write("INVALID_LEVEL", "test message")

    def test_regex_ticket_id_validation(self):
        self.assertFalse(validate_ticket_id("not-a-ticket"))
        self.assertFalse(validate_ticket_id("TKT-ZZZZZZZZ"))  # non-hex
        # Valid IDs start with TKT- followed by 8 hex chars
        self.assertTrue(validate_ticket_id("TKT-ABCDEF12"))

    def test_regex_email_validation(self):
        self.assertTrue(validate_email("alice@technova.com"))
        self.assertFalse(validate_email("not-an-email"))

    def test_regex_date_validation(self):
        self.assertTrue(validate_date("2024-01-15"))
        self.assertFalse(validate_date("15-01-2024"))
        self.assertFalse(validate_date("not-a-date"))



# ADVANCED PYTHON FEATURES

class TestAdvancedPython(unittest.TestCase):

    def setUp(self):
        self.tm = TicketManager()
        self.tm.create_ticket("A", "IT", "Server issue", "Server Down",   "Incident", impact="High")
        self.tm.create_ticket("B", "HR", "Password",     "Password Reset","ServiceRequest")
        self.tm.create_ticket("C", "IT", "CPU high",     "High CPU Usage","Incident", impact="High")

    def test_iterator(self):
        """TicketIterator correctly iterates all tickets."""
        tickets = self.tm.get_all_tickets()
        it   = TicketIterator(tickets)
        seen = []
        for t in it:
            seen.append(t.ticket_id)
        self.assertEqual(len(seen), len(tickets))

    def test_iterator_stops(self):
        """TicketIterator raises StopIteration correctly."""
        it = TicketIterator([])
        with self.assertRaises(StopIteration):
            next(it)

    def test_generator_pending_tickets(self):
        """pending_tickets_generator yields only open/in-progress."""
        gen = self.tm.pending_tickets_generator()
        tickets = list(gen)
        for t in tickets:
            self.assertIn(t.status, ("Open", "In Progress"))

    def test_priority_label_generator(self):
        """priority_label_generator yields 4 tuples."""
        items = list(priority_label_generator())
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0], ("P1", "Critical", "1 Hour"))

    def test_map_to_ids(self):
        tickets = self.tm.get_all_tickets()
        ids = map_to_ids(tickets)
        self.assertEqual(len(ids), len(tickets))
        for i in ids:
            self.assertTrue(i.startswith("TKT-"))

    def test_filter_open_tickets(self):
        tickets = self.tm.get_all_tickets()
        open_t  = filter_open_tickets(tickets)
        for t in open_t:
            self.assertEqual(t.status, "Open")

    def test_count_by_priority_reduce(self):
        tickets = self.tm.get_all_tickets()
        counts  = count_by_priority(tickets)
        self.assertIsInstance(counts, dict)
        total = sum(counts.values())
        self.assertEqual(total, len(tickets))

    def test_unique_categories_set(self):
        cats = self.tm.get_unique_categories()
        self.assertIsInstance(cats, set)
        self.assertGreater(len(cats), 0)

    def test_ticketmanager_len(self):
        self.assertGreaterEqual(len(self.tm), 3)

    def test_ticketmanager_iterable(self):
        count = 0
        for t in self.tm:
            count += 1
        self.assertEqual(count, len(self.tm))

    def test_report_generator_yields_lines(self):
        rg    = ReportGenerator(self.tm)
        lines = list(rg.report_line_generator("daily"))
        self.assertGreater(len(lines), 0)
        self.assertTrue(any("DAILY REPORT" in l for l in lines))

    def test_logger_search_logs(self):
        logger = Logger()
        log_event("INFO", "TEST_UNIQUE_MARKER_XYZ")
        results = logger.search_logs("TEST_UNIQUE_MARKER_XYZ")
        self.assertGreater(len(results), 0)

    def test_logger_count_by_level(self):
        logger = Logger()
        counts = logger.count_by_level()
        self.assertIsInstance(counts, dict)


# ITIL WORKFLOWS

class TestITILWorkflows(unittest.TestCase):

    def setUp(self):
        self.mgr = ITILManager()
        self.tm  = TicketManager()

    def test_create_incident(self):
        inc = self.mgr.create_incident(
            "Server Outage", "Server Down", "Prod server down", "Alice")
        self.assertIsNotNone(inc)
        self.assertTrue(inc.record_id.startswith("INC-"))
        self.assertEqual(inc.priority, "P1")

    def test_create_service_request(self):
        sr = self.mgr.create_service_request(
            "Password Reset", "Password Reset", "Need new password", "Bob")
        self.assertTrue(sr.record_id.startswith("SRQ-"))
        self.assertEqual(sr.priority, "P4")

    def test_create_change_request(self):
        cr = self.mgr.create_change_request(
            "Patch Deploy", "Other", "Apply security patch", "Dave",
            change_type="Normal", change_reason="Security", cab_required=True)
        self.assertTrue(cr.record_id.startswith("CHG-"))
        self.assertFalse(cr.cab_approved)

    def test_problem_detection_from_tickets(self):
        """5+ same-category open tickets → ProblemRecord created."""
        for i in range(5):
            self.tm.create_ticket(f"User{i}", "Ops",
                                  "Printer broken", "Printer Issue",
                                  "Incident", impact="Low")
        problems = self.mgr.detect_problems_from_tickets(self.tm)
        self.assertGreater(len(problems), 0)
        cats = [p.category for p in problems]
        self.assertIn("Printer Issue", cats)

    def test_itil_record_serialisation(self):
        inc = self.mgr.create_incident(
            "Test", "Laptop Slow", "Very slow laptop", "Carol")
        d   = inc.to_dict()
        self.assertEqual(d["type"], "Incident")
        self.assertEqual(d["category"], "Laptop Slow")

    def test_itil_special_methods(self):
        inc = self.mgr.create_incident(
            "Test", "Server Down", "Crash", "X")
        self.assertIn("INC-", str(inc))
        self.assertIn("Incident", repr(inc))
        self.assertEqual(inc, inc)

    def test_ticket_iterator_in_itil(self):
        """TicketIterator works over ITIL records."""
        from itil import TicketIterator as ITILIter
        recs = self.mgr.get_all()
        it   = ITILIter(recs)
        seen = list(it)
        self.assertEqual(len(seen), len(recs))

    def test_sla_generator(self):
        """sla_breach_generator is a generator."""
        import types
        gen = self.mgr.sla_breach_generator()
        self.assertIsInstance(gen, types.GeneratorType)

    def test_summary_stats(self):
        stats = self.mgr.summary_stats()
        self.assertIn("total", stats)
        self.assertIn("by_type", stats)



# MAIN

if __name__ == "__main__":
    # Clear test tickets before running
    print("=" * 60)
    print("  Smart IT Service Desk — Test Suite")
    print("=" * 60)

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestTicketCreation,
        TestPriorityLogic,
        TestSLABreach,
        TestAutoMonitoring,
        TestFileHandling,
        TestSearchTicket,
        TestExceptionHandling,
        TestAdvancedPython,
        TestITILWorkflows,
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print(f"  Tests Run     : {result.testsRun}")
    print(f"  Passed        : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures      : {len(result.failures)}")
    print(f"  Errors        : {len(result.errors)}")
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)