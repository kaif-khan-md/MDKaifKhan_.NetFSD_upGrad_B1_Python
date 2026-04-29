"""
reports.py - Report Generator
Daily Summary, Monthly Trend, Escalation Report.
Advanced Python: map, filter, reduce, generators, list comprehensions,
                 Counter, defaultdict, sorted with key.
"""

from datetime import datetime
from collections import Counter, defaultdict
from functools import reduce

from utils import log_event, print_header, print_separator


class ReportGenerator:
    """
    Generates daily, monthly, and escalation reports.
    Demonstrates: encapsulation, static methods, generators,
    map/filter/reduce, list comprehensions.
    
    """

    def __init__(self, ticket_manager):
        self.__tm = ticket_manager

    
    #  Daily Summary Report
    
    def daily_summary(self, date: str | None = None) -> dict:
        """Generate daily summary for a given date (YYYY-MM-DD), default today."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        all_tickets  = self.__tm.get_all_tickets()

        # List comprehension: filter by date
        day_tickets  = [t for t in all_tickets if t.created_at.startswith(date)]

        # map + filter to count statuses
        open_t       = list(filter(lambda t: t.status == "Open",        day_tickets))
        inprog_t     = list(filter(lambda t: t.status == "In Progress", day_tickets))
        closed_t     = list(filter(lambda t: t.status == "Closed",      day_tickets))
        high_prio    = list(filter(lambda t: t.priority in ("P1","P2"), day_tickets))
        sla_breached = list(filter(lambda t: t.sla_breached,            day_tickets))

        # reduce: count by department
        dept_counts  = reduce(
            lambda acc, t: {**acc, t.department: acc.get(t.department, 0) + 1},
            day_tickets, {}
        )

        report = {
            "date":         date,
            "total":        len(day_tickets),
            "open":         len(open_t),
            "in_progress":  len(inprog_t),
            "closed":       len(closed_t),
            "high_priority":len(high_prio),
            "sla_breached": len(sla_breached),
            "dept_counts":  dept_counts,
            "tickets":      day_tickets,
        }
        log_event("INFO", f"Daily summary generated for {date}: {len(day_tickets)} tickets")
        return report

    def print_daily_summary(self, date: str | None = None):
        r = self.daily_summary(date)
        print_header(f"Daily Summary Report  {r['date']}")

        rows = [
            ("Total Tickets Raised",   r["total"],         "*"),
            ("Open Tickets",           r["open"],          "O"),
            ("In Progress",            r["in_progress"],   ">"),
            ("Closed Tickets",         r["closed"],        "C"),
            ("High Priority (P1/P2)",  r["high_priority"], "!"),
            ("SLA Breached",           r["sla_breached"],  "X"),
        ]

        for label, count, icon in rows:
            bar = "#" * min(count * 3, 36)
            print(f"  [{icon}] {label:<28} {count:>4}  {bar}")

        print_separator()

        if r["dept_counts"]:
            print("  DEPARTMENT BREAKDOWN:")
            for dept, cnt in sorted(r["dept_counts"].items(),
                                    key=lambda x: x[1], reverse=True):
                bar = "#" * min(cnt * 2, 30)
                print(f"    {dept:<18} {cnt:>3}  {bar}")
            print_separator()

        if r["tickets"]:
            print("  TICKET LIST:")
            print(f"  {'ID':<14} {'P':<4} {'Status':<14} {'Type':<16} {'Employee':<18} {'Category'}")
            print_separator()
            for t in r["tickets"]:
                sla = " [SLA!]" if t.sla_breached else ""
                print(f"  {t.ticket_id:<14} {t.priority:<4} {t.status:<14} "
                      f"{t.ticket_type:<16} {t.employee_name[:16]:<18} {t.category}{sla}")
        else:
            print("  No tickets found for this date.")
        print_separator()

    
    # Monthly Trend Report
    
    def monthly_trend(self, year: int | None = None, month: int | None = None) -> dict:
        """Generate monthly trend report."""
        now = datetime.now()
        year  = year  or now.year
        month = month or now.month

        prefix      = f"{year:04d}-{month:02d}"
        all_tickets = self.__tm.get_all_tickets()

        # List comprehension + filter
        month_tickets = [t for t in all_tickets if t.created_at.startswith(prefix)]

        # Counter for most common issues and departments
        cat_counter  = Counter(map(lambda t: t.category,   month_tickets))
        dept_counter = Counter(map(lambda t: t.department, month_tickets))

        most_common_issues = cat_counter.most_common(5)
        busiest_dept       = dept_counter.most_common(1)[0] if dept_counter else ("N/A", 0)

        # Average resolution time 
        res_times = [t.get_resolution_hours() for t in month_tickets
                     if t.get_resolution_hours() is not None]
        avg_resolution = round(sum(res_times) / len(res_times), 2) if res_times else 0

        # Priority breakdown using reduce
        priority_breakdown = reduce(
            lambda acc, t: {**acc, t.priority: acc.get(t.priority, 0) + 1},
            month_tickets, {}
        )

        # Daily counts 
        daily_counts: dict[str, int] = defaultdict(int)
        for t in month_tickets:
            daily_counts[t.created_at[:10]] += 1

        # Repeated problems (categories with 3+ tickets)
        repeated_problems = {cat: cnt for cat, cnt in cat_counter.items() if cnt >= 3}

        report = {
            "month":              prefix,
            "total":              len(month_tickets),
            "most_common_issues": most_common_issues,
            "avg_resolution_hrs": avg_resolution,
            "busiest_department": busiest_dept,
            "priority_breakdown": priority_breakdown,
            "daily_counts":       dict(sorted(daily_counts.items())),
            "sla_breached":       sum(1 for t in month_tickets if t.sla_breached),
            "repeated_problems":  repeated_problems,
        }
        log_event("INFO", f"Monthly trend report generated for {prefix}")
        return report

    def print_monthly_trend(self, year: int | None = None, month: int | None = None):
        r = self.monthly_trend(year, month)
        print_header(f"Monthly Trend Report  {r['month']}")

        print(f"  Total Tickets        : {r['total']}")
        print(f"  Avg Resolution Time  : {r['avg_resolution_hrs']} hrs")
        print(f"  Busiest Department   : {r['busiest_department'][0]} "
              f"({r['busiest_department'][1]} tickets)")
        print(f"  SLA Breached         : {r['sla_breached']}")
        print_separator()

        print("  TOP ISSUES:")
        for cat, count in r["most_common_issues"]:
            bar = "#" * min(count * 2, 36)
            print(f"    {cat:<28} {count:>3}  {bar}")

        print_separator()
        print("  PRIORITY BREAKDOWN:")
        for p in ["P1", "P2", "P3", "P4"]:
            count = r["priority_breakdown"].get(p, 0)
            bar   = "#" * min(count * 2, 36)
            labels = {"P1": "P1-Critical", "P2": "P2-High",
                      "P3": "P3-Medium",   "P4": "P4-Low"}
            print(f"    {labels[p]:<14} {count:>3}  {bar}")

        print_separator()
        if r["repeated_problems"]:
            print("  REPEATED PROBLEMS (3+ occurrences):")
            for cat, cnt in sorted(r["repeated_problems"].items(),
                                   key=lambda x: x[1], reverse=True):
                print(f"    {cat:<28} {cnt:>3} occurrences")
            print_separator()

        if r["daily_counts"]:
            print("  DAILY TICKET VOLUME:")
            for day, count in r["daily_counts"].items():
                bar = "-" * count
                print(f"    {day}  {count:>3}  {bar}")
        print_separator()

    
    #  Escalation Report
    
    def print_escalation_report(self):
        print_header("Escalation & SLA Breach Report")
        alerts   = self.__tm.check_all_escalations()
        breached = self.__tm.check_all_sla()

        if not alerts and not breached:
            print("  No escalations or SLA breaches detected.")
        else:
            if alerts:
                print(f"  ESCALATION ALERTS ({len(alerts)}):")
                for a in alerts:
                    print(f"    {a}")
            if breached:
                print(f"\n  SLA BREACHED TICKETS ({len(breached)}):")
                for t in breached:
                    print(f"    {t.ticket_id} | {t.priority} | "
                          f"{t.category} | {t.employee_name}")
        print_separator()


    #  Generator: stream report lines

    def report_line_generator(self, report_type: str = "daily"):
        """
        Generator that yields formatted report lines one at a time.
        Demonstrates: generators.
        """
        if report_type == "daily":
            r = self.daily_summary()
            yield f"=== DAILY REPORT {r['date']} ==="
            yield f"Total: {r['total']}"
            yield f"Open: {r['open']}"
            yield f"Closed: {r['closed']}"
            yield f"High Priority: {r['high_priority']}"
            yield f"SLA Breached: {r['sla_breached']}"
        elif report_type == "monthly":
            r = self.monthly_trend()
            yield f"=== MONTHLY REPORT {r['month']} ==="
            yield f"Total: {r['total']}"
            yield f"Avg Resolution: {r['avg_resolution_hrs']} hrs"
            for issue, cnt in r["most_common_issues"]:
                yield f"  Issue: {issue} ({cnt}x)"

    # Static helper
    @staticmethod
    def format_table_row(cols: list, widths: list) -> str:
        """Static method: format a table row with given column widths."""
        return "  " + "  ".join(str(c).ljust(w) for c, w in zip(cols, widths))