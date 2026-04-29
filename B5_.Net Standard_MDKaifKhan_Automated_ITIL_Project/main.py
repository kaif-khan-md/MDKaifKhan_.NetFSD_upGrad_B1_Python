"""
main.py - Smart IT Service Desk & System Monitoring Automation
Entry Point

Debugging notes:
  Breakpoints   : Set in create_ticket(), __load_tickets(), check_sla() in IDE
  Variable Watch: Watch ticket.to_dict() to verify priority auto-assignment
  Call Stack    : Inspect stack when EmptyFieldError/DuplicateTicketError raised
  Step Execution: Step through TicketManager.__load_tickets() JSON parsing loop
  Real-time logs: All events written to data/logs.txt for post-mortem analysis
"""

import sys
import os
from datetime import datetime

from tickets  import TicketManager
from monitor  import Monitor
from reports  import ReportGenerator
from itil     import ITILManager
from logger   import Logger, get_logger, log_event as _log
from utils    import (
    print_header, print_separator, backup_tickets_to_csv,
    select_from_list, input_non_empty, view_logs,
    CATEGORY_MAP, TICKET_TYPE_MAP, DEPARTMENTS, STATUS_OPTIONS,
    format_priority_badge, format_status_badge,
    priority_label_generator,         # generator
    filter_open_tickets, map_to_ids,  # map/filter helpers
    count_by_priority,                 # reduce helper
)

# ─────────────────────────────────────────────
#  Global singletons
# ─────────────────────────────────────────────
tm         = TicketManager()
monitor    = Monitor()
report_gen = ReportGenerator(tm)
itil_mgr   = ITILManager()
logger     = get_logger()


#Ticket Operations

def menu_create_ticket():
    print_header("Create New Ticket")
    try:
        emp_name = input_non_empty("  Employee Name     : ")

        print("\n  Department:")
        for i, d in enumerate(DEPARTMENTS, 1):
            print(f"    {i:>2}. {d}")
        while True:
            try:
                d_choice = int(input("  Enter number: "))
                if 1 <= d_choice <= len(DEPARTMENTS):
                    department = DEPARTMENTS[d_choice - 1]
                    break
                print("  Invalid choice.")
            except ValueError:
                print("  Please enter a number.")

        category    = select_from_list("Issue Category", CATEGORY_MAP)
        issue_desc  = input_non_empty("  Issue Description : ")
        ticket_type = select_from_list("Ticket Type", TICKET_TYPE_MAP)

        kwargs: dict = {}
        if ticket_type == "Incident":
            kwargs["impact"] = select_from_list(
                "Impact Level", {"1": "Low", "2": "Medium", "3": "High"})
        elif ticket_type == "ServiceRequest":
            kwargs["requested_service"] = (
                input("  Requested Service (optional): ").strip() or "General")
        elif ticket_type == "ChangeRequest":
            kwargs["change_reason"] = (
                input("  Change Reason (optional): ").strip() or "Not specified")

        ticket = tm.create_ticket(emp_name, department, issue_desc,
                                  category, ticket_type, **kwargs)
        print(f"\n  Ticket created successfully!")
        ticket.display()
        logger.info(f"Ticket created via UI: {ticket.ticket_id}")

    except Exception as e:
        print(f"\n  Error: {e}")
        logger.error(f"Ticket creation UI error: {e}")


def menu_view_all_tickets():
    print_header("All Tickets")
    tickets = tm.get_all_tickets()
    if not tickets:
        print("  No tickets found.")
        return

    # sorted() with key
    tickets_sorted = sorted(
        tickets,
        key=lambda t: ({"P1": 0, "P2": 1, "P3": 2, "P4": 3}.get(t.priority, 9),
                       t.created_at)
    )

    print(f"  {'ID':<14} {'P':<4} {'Status':<14} {'Type':<16} {'Employee':<18} {'Category':<22} SLA")
    print_separator()
    for t in tickets_sorted:
        sla = "BREACH" if t.sla_breached else "OK"
        print(f"  {t.ticket_id:<14} {t.priority:<4} {t.status:<14} "
              f"{t.ticket_type:<16} {t.employee_name[:16]:<18} "
              f"{t.category[:20]:<22} {sla}")
    print_separator()
    print(f"  Total: {len(tickets)} tickets")

    #map/filter/reduce
    open_ids   = map_to_ids(filter_open_tickets(tickets))
    by_priority = count_by_priority(tickets)
    print(f"  Open ticket IDs: {len(open_ids)}")
    print(f"  By Priority: {by_priority}")


def menu_search_ticket():
    print_header("Search Ticket by ID")
    try:
        tid = input("  Enter Ticket ID: ").strip()
        if not tid:
            raise ValueError("Ticket ID cannot be empty.")
            
        ticket = tm.search_by_id(tid)
        if ticket:
            ticket.display()
            if ticket.notes:
                print("  Notes:")
                for n in ticket.notes:
                    print(f"    {n}")
        else:
            print(f"  Ticket '{tid}' not found.")
            logger.warning(f"Search: ticket not found: {tid}")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_update_status():
    print_header("Update Ticket Status")
    try:
        tid = input("  Enter Ticket ID: ").strip()
        if not tid:
            raise ValueError("Ticket ID cannot be empty.")
        ticket = tm.search_by_id(tid)
        if not ticket:
            print(f"  Ticket '{tid}' not found.")
            return
        print(f"  Current Status: {ticket.status}")
        new_status = select_from_list("New Status", STATUS_OPTIONS)
        tm.update_status(tid, new_status)
        print(f"  Status updated to: {new_status}")
    except ValueError as e:
        print(f"  Error: {e}")
    except Exception as e:
        print(f"  Error: {e}")
        logger.error(f"Status update error: {e}")


def menu_close_ticket():
    print_header("Close Ticket")
    try:
        tid = input("  Enter Ticket ID to close: ").strip()
        if not tid:
            raise ValueError("Ticket ID cannot be empty.")
        ticket = tm.search_by_id(tid)
        if not ticket:
            print(f"  Ticket '{tid}' not found.")
            return
        if ticket.status == "Closed":
            print("  Ticket is already closed.")
            return
        confirm = input(f"  Close ticket {tid}? (y/n): ").strip().lower()
        if confirm == "y":
            tm.close_ticket(tid)
            print(f"  Ticket {tid} has been closed.")
        else:
            print("  Cancelled.")
    except ValueError as e:
        print(f"  Error: {e}")


def menu_delete_ticket():
    print_header("Delete Ticket")
    try:
        tid = input("  Enter Ticket ID to delete: ").strip()
        if not tid:
            raise ValueError("Ticket ID cannot be empty.")
        ticket = tm.search_by_id(tid)
        if not ticket:
            print(f"  Ticket '{tid}' not found.")
            return
        print(f"  {ticket}")
        confirm = input("  Permanently delete? (y/n): ").strip().lower()
        if confirm == "y":
            tm.delete_ticket(tid)
            print(f"  Ticket {tid} deleted.")
        else:
            print("  Cancelled.")
    except ValueError as e:
        print(f"  Error: {e}")


# SLA

def menu_sla_check():
    print_header("SLA Status Check")
    breached  = tm.check_all_sla()
    alerts    = tm.check_all_escalations()

    # Use generator to show pending tickets
    print("  PENDING TICKETS (generator):")
    for t in tm.pending_tickets_generator():
        elapsed = t.get_elapsed_hours()
        sla_hrs = {"P1": 1, "P2": 4, "P3": 8, "P4": 24}.get(t.priority, 24)
        remaining = sla_hrs - elapsed
        status_str = f"OVERDUE {abs(remaining):.1f}h" if remaining < 0 else f"{remaining:.1f}h left"
        print(f"    {t.ticket_id} | {t.priority} | {t.category[:20]:<22} | {status_str}")

    print_separator()
    if not breached and not alerts:
        print("  All tickets within SLA limits. No escalations.")
        return

    if breached:
        print(f"\n  SLA BREACHED ({len(breached)}):")
        for t in breached:
            print(f"    {t.ticket_id} | {t.priority} | {t.category} "
                  f"| Created: {t.created_at[:19]}")
    if alerts:
        print(f"\n  ESCALATION ALERTS ({len(alerts)}):")
        for a in alerts:
            print(f"    {a}")


# System Monitor


def menu_system_monitor():
    print_header("System Health Monitor")
    print("  Collecting system metrics...")
    stats, alerts, created = monitor.run_full_check(tm)
    monitor.display_stats(stats)
    monitor.display_alerts(alerts)
    if created:
        print(f"\n  Auto-created {len(created)} support ticket(s):")
        for t in created:
            print(f"    {t.ticket_id} | {t.priority} | {t.category}")

    # Show average CPU from history
    avg_cpu = monitor.avg_cpu_from_history()
    print(f"\n  Average CPU (this session): {avg_cpu}%")


# ITIL Menu


def menu_itil():
    print_header("ITIL Workflow Manager")
    itil_menu = {
        "1": "Create Incident",
        "2": "Create Service Request",
        "3": "Create Change Request",
        "4": "View All ITIL Records",
        "5": "ITIL SLA & Escalations",
        "6": "Detect Problem Records (Recurring Issues)",
        "7": "View Problem Records",
        "8": "ITIL Summary Stats",
        "0": "Back",
    }
    for k, v in itil_menu.items():
        print(f"  {k}. {v}")

    choice = input("\n  Enter choice: ").strip()

    if choice == "1":
        _itil_create_incident()
    elif choice == "2":
        _itil_create_sr()
    elif choice == "3":
        _itil_create_cr()
    elif choice == "4":
        records = itil_mgr.get_all()
        if not records:
            print("  No ITIL records found.")
        else:
            for r in records:
                print(f"  {r}")
    elif choice == "5":
        itil_mgr.display_sla_report()
    elif choice == "6":
        problems = itil_mgr.detect_problems_from_tickets(tm)
        if problems:
            print(f"  Created {len(problems)} Problem Record(s):")
            for p in problems:
                print(f"    {p.record_id} | {p.category} | {p.recurrence_count}x")
        else:
            print("  No recurring issues detected (need 5+ same category).")
    elif choice == "7":
        recs = itil_mgr.get_by_type("ProblemRecord")
        if not recs:
            print("  No Problem Records found.")
        for r in recs:
            r.display()
    elif choice == "8":
        stats = itil_mgr.summary_stats()
        print(f"\n  Total Records  : {stats['total']}")
        print(f"  Open           : {stats['open']}")
        print(f"  P1 (Critical)  : {stats['p1']}")
        print(f"  SLA Breached   : {stats['breached']}")
        print(f"  By Type        : {stats['by_type']}")
    elif choice == "0":
        return
    else:
        print("  Invalid choice.")


def _itil_create_incident():
    print_header("Create ITIL Incident")
    try:
        title    = input_non_empty("  Title      : ")
        category = select_from_list("Category", CATEGORY_MAP)
        desc     = input_non_empty("  Description: ")
        creator  = input_non_empty("  Created By : ")
        impact   = select_from_list("Impact", {"1":"Low","2":"Medium","3":"High"})
        urgency  = select_from_list("Urgency", {"1":"Low","2":"Medium","3":"High"})
        inc = itil_mgr.create_incident(title, category, desc, creator, impact, urgency)
        inc.display()
    except Exception as e:
        print(f"  Error: {e}")
        logger.error(f"ITIL incident creation error: {e}")


def _itil_create_sr():
    print_header("Create ITIL Service Request")
    try:
        title   = input_non_empty("  Title        : ")
        category = select_from_list("Category", CATEGORY_MAP)
        desc    = input_non_empty("  Description  : ")
        creator = input_non_empty("  Created By   : ")
        stype   = input("  Service Type (optional): ").strip() or "General"
        sr = itil_mgr.create_service_request(title, category, desc, creator, stype)
        sr.display()
    except Exception as e:
        print(f"  Error: {e}")


def _itil_create_cr():
    print_header("Create ITIL Change Request")
    try:
        title   = input_non_empty("  Title        : ")
        category = select_from_list("Category", CATEGORY_MAP)
        desc    = input_non_empty("  Description  : ")
        creator = input_non_empty("  Created By   : ")
        ctype   = select_from_list("Change Type",
                                   {"1":"Standard","2":"Normal","3":"Emergency"})
        reason  = input("  Reason (optional): ").strip() or "Not specified"
        cab     = input("  CAB Required? (y/n): ").strip().lower() == "y"
        cr = itil_mgr.create_change_request(title, category, desc, creator,
                                            ctype, reason, cab)
        cr.display()
    except Exception as e:
        print(f"  Error: {e}")


# Reports

def menu_daily_report():
    print_header("Daily Summary Report")
    date = input("  Date (YYYY-MM-DD) [Enter for today]: ").strip() or None
    try:
        report_gen.print_daily_summary(date)
    except Exception as e:
        print(f"  Error: {e}")
        logger.error(f"Daily report error: {e}")


def menu_monthly_report():
    print_header("Monthly Trend Report")
    try:
        yr = input("  Year  [Enter for current]: ").strip()
        mo = input("  Month [Enter for current]: ").strip()
        year  = int(yr) if yr.isdigit() else None
        month = int(mo) if mo.isdigit() else None
        report_gen.print_monthly_trend(year, month)
    except ValueError:
        print("  Invalid year/month.")
    except Exception as e:
        print(f"  Error: {e}")


def menu_escalation_report():
    report_gen.print_escalation_report()


# Utilities

def menu_backup():
    print_header("Backup Tickets to CSV")
    backup_tickets_to_csv()


def menu_view_logs():
    print_header("System Logs")
    try:
        n = input("  Recent entries to show? [default 30]: ").strip()
        n = int(n) if n.isdigit() else 30
        lvl = input("  Filter level (INFO/WARNING/ERROR/CRITICAL) [Enter=all]: ").strip().upper()
        lvl = lvl if lvl in ("INFO","WARNING","ERROR","CRITICAL") else None
        logger.print_recent(n, lvl)

        # Log level counts using map/filter/reduce
        counts = logger.count_by_level()
        print(f"\n  Log entry counts: {counts}")
    except Exception as e:
        print(f"  Error: {e}")


def menu_problem_management():
    print_header("Problem Management (Tickets Module)")
    print("  Scanning for recurring issues (5+ occurrences)...")
    problems = tm.check_problem_records()
    if problems:
        print(f"\n  Created {len(problems)} Problem Record(s):")
        for p in problems:
            print(f"    {p.ticket_id} | {p.category} | {p.recurrence_count}x")
    else:
        print("  No recurring issues found (need 5+ same category open tickets).")


def menu_priority_reference():
    """Show priority/SLA reference using generator."""
    print_header("Priority & SLA Reference")
    for priority, label, sla in priority_label_generator():
        print(f"  {priority} ({label:<10}) : SLA = {sla}")

    print_separator()
    print("  CURRENT TICKET COUNT BY PRIORITY:")
    by_prio = tm.count_by_priority()
    for p in ["P1","P2","P3","P4"]:
        cnt = by_prio.get(p, 0)
        bar = "#" * cnt
        print(f"    {p}: {cnt:>3}  {bar}")


def menu_advanced_demo():
    """Demonstrates advanced Python features for evaluation."""
    print_header("Advanced Python Demo")
    tickets = tm.get_all_tickets()
    if not tickets:
        print("  No tickets to demonstrate on. Create some first.")
        return

    # Iterators
    print("  [Iterator] Iterating via TicketIterator:")
    from tickets import TicketIterator
    it = TicketIterator(tickets[:3])
    for t in it:
        print(f"    {t.ticket_id} | {t.priority}")

    # Generators
    print("\n  [Generator] Pending tickets (generator):")
    for t in tm.pending_tickets_generator():
        print(f"    {t.ticket_id} | {t.status}")
        break  # just show first one

    # Generator: report lines
    print("\n  [Generator] Report lines (generator):")
    for line in report_gen.report_line_generator("daily"):
        print(f"    {line}")

    # map / filter / reduce
    print("\n  [map]    All IDs:", map_to_ids(tickets[:3]))
    print("  [filter] Open tickets:", len(filter_open_tickets(tickets)))
    print("  [reduce] Count by priority:", count_by_priority(tickets))

    # list / set / dict comprehensions
    categories = list({t.category for t in tickets})
    print(f"\n  [Set comprehension] Unique categories: {categories}")

    high_prio_ids = [t.ticket_id for t in tickets if t.priority in ("P1","P2")]
    print(f"  [List comprehension] P1/P2 ticket IDs: {high_prio_ids}")

    dept_ticket_map = {t.ticket_id: t.department for t in tickets[:5]}
    print(f"  [Dict comprehension] ID→Dept map: {dept_ticket_map}")

    # Tuples
    summary_tuple = tuple((t.ticket_id, t.priority) for t in tickets[:3])
    print(f"\n  [Tuple] Summary tuple: {summary_tuple}")

    # String handling
    ids_upper = list(map(lambda x: x.upper(), map_to_ids(tickets[:2])))
    print(f"  [String] Upper IDs: {ids_upper}")

    # len / contains (special methods)
    print(f"\n  [Special methods] len(tm)={len(tm)}, "
          f"'TKT-XXXXXXXX' in tm={('TKT-XXXXXXXX' in tm)}")


# Main Menu

MAIN_MENU = """
--------------------------------------------------
SMART IT SERVICE DESK
--------------------------------------------------
TICKET MANAGEMENT
1. Create New Ticket
2. View All Tickets
3. Search Ticket by ID
4. Update Ticket Status
5. Close Ticket
6. Delete Ticket
--------------------------------------------------
SLA & ESCALATION
7. Check SLA Status & Pending Tickets
--------------------------------------------------
SYSTEM MONITORING
8. Run System Health Monitor
--------------------------------------------------
ITIL WORKFLOWS
9. ITIL Manager (Incident / SR / Problem / Change)
--------------------------------------------------
REPORTS
10. Daily Summary Report
11. Monthly Trend Report
12. Escalation Report
--------------------------------------------------
UTILITIES
13. Problem Management (Auto-detect recurring)
14. Backup Tickets to CSV
15. View Logs
16. Priority / SLA Reference
17. Advanced Python Demo
--------------------------------------------------
0. Exit
"""

MENU_ACTIONS: dict = {
    "1":  menu_create_ticket,
    "2":  menu_view_all_tickets,
    "3":  menu_search_ticket,
    "4":  menu_update_status,
    "5":  menu_close_ticket,
    "6":  menu_delete_ticket,
    "7":  menu_sla_check,
    "8":  menu_system_monitor,
    "9":  menu_itil,
    "10": menu_daily_report,
    "11": menu_monthly_report,
    "12": menu_escalation_report,
    "13": menu_problem_management,
    "14": menu_backup,
    "15": menu_view_logs,
    "16": menu_priority_reference,
    "17": menu_advanced_demo,
}


def main():
    logger.info("=== Smart IT Service Desk Started ===")
    print("\n  Welcome to TechNova Solutions — Smart IT Service Desk")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        print(MAIN_MENU)
        try:
            choice = input("\n  Enter your choice: ").strip()

            if choice == "0":
                backup_tickets_to_csv()
                logger.info("=== Application exited gracefully ===")
                print("\n  Goodbye! Backup saved.\n")
                sys.exit(0)

            if choice not in MENU_ACTIONS:
                raise ValueError(f"Invalid menu option: '{choice}'")

            MENU_ACTIONS[choice]()

        except ValueError as e:
            print(f"\n  Error: {e}. Please enter 0-17.")
            logger.error(f"Invalid menu input: {e}")
        except KeyboardInterrupt:
            print("\n\n  Interrupted. Saving data...")
            tm.save_tickets()
            backup_tickets_to_csv()
            logger.info("Application interrupted by user (Ctrl+C)")
            sys.exit(0)
        except Exception as e:
            print(f"\n  Unexpected error: {e}")
            logger.error(f"Unhandled exception in main loop: {e}")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()