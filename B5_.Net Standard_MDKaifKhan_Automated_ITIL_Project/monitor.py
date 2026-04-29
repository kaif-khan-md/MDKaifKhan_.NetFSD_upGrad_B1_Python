"""
monitor.py - System Health Monitor
Monitors: CPU, RAM, Disk, Network
Auto-generates P1 tickets on threshold breach.
Advanced Python: generators, decorators, map/filter, psutil.

"""

import psutil
from datetime import datetime
from utils import log_event, ascii_bar, print_header, print_separator


# Thresholds

THRESHOLDS: dict = {
    "cpu_percent":       90.0,
    "ram_percent":       95.0,
    "disk_free_percent": 10.0,
}

# Network baseline (bytes) – compared between snapshots
_net_baseline: dict | None = None



#  Monitor Class

class Monitor:
    """
    System monitor. Demonstrates: encapsulation, static methods,
    generators, decorators, map/filter.
    """

    def __init__(self):
        self.__last_check: datetime | None = None
        self.__alerts: list[dict]          = []
        self.__history: list[dict]         = []   # list of past stat snapshots

    # Properties
    @property
    def last_check(self):  return self.__last_check
    @property
    def alerts(self):      return list(self.__alerts)
    @property
    def history(self):     return list(self.__history)

    # Collect stats
    def get_system_stats(self) -> dict:
        """Collect all system metrics."""
        try:
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net  = psutil.net_io_counters()

            stats = {
                "cpu_percent":        cpu,
                "ram_percent":        ram.percent,
                "ram_used_gb":        round(ram.used   / (1024**3), 2),
                "ram_total_gb":       round(ram.total  / (1024**3), 2),
                "disk_total_gb":      round(disk.total / (1024**3), 2),
                "disk_used_gb":       round(disk.used  / (1024**3), 2),
                "disk_free_gb":       round(disk.free  / (1024**3), 2),
                "disk_used_percent":  disk.percent,
                "disk_free_percent":  round(100 - disk.percent, 2),
                "net_bytes_sent_mb":  round(net.bytes_sent / (1024**2), 2),
                "net_bytes_recv_mb":  round(net.bytes_recv / (1024**2), 2),
                "net_packets_sent":   net.packets_sent,
                "net_packets_recv":   net.packets_recv,
                "timestamp":          datetime.now().isoformat(),
            }
            self.__last_check = datetime.now()
            self.__history.append(stats)
            # Keep only last 100 snapshots
            if len(self.__history) > 100:
                self.__history = self.__history[-100:]
            return stats

        except Exception as e:
            log_event("ERROR", f"System stats collection failed: {e}")
            return {}

    # Threshold check
    def check_thresholds(self, stats: dict) -> list[dict]:
        """Returns list of alert dicts for breached thresholds."""
        alerts: list[dict] = []
        if not stats:
            return alerts

        checks = [
            ("cpu_percent",       stats.get("cpu_percent", 0),
             THRESHOLDS["cpu_percent"],
             "High CPU Usage",
             f"CPU critically high at {stats.get('cpu_percent', 0):.1f}%"),

            ("ram_percent",       stats.get("ram_percent", 0),
             THRESHOLDS["ram_percent"],
             "Server Down",
             f"RAM critically high at {stats.get('ram_percent', 0):.1f}%"),
        ]

        for metric, value, threshold, category, desc in checks:
            if value > threshold:
                alerts.append({"metric": metric, "value": value,
                                "threshold": threshold, "category": category,
                                "description": desc})

        disk_free = stats.get("disk_free_percent", 100)
        if disk_free < THRESHOLDS["disk_free_percent"]:
            alerts.append({
                "metric": "disk_free_percent",
                "value": disk_free,
                "threshold": THRESHOLDS["disk_free_percent"],
                "category": "Disk Space Full",
                "description": f"Disk free space critically low at {disk_free:.1f}%",
            })

        self.__alerts = alerts
        return alerts

    # Generator: stream alerts
    def alert_generator(self, stats: dict):
        """Generator that yields one alert dict at a time."""
        alerts = self.check_thresholds(stats)
        for alert in alerts:
            yield alert

    # Auto-ticket creation
    def auto_create_tickets(self, alerts: list[dict], ticket_manager) -> list:
        """Auto-creates P1 tickets for each breached threshold."""
        created = []
        for alert in alerts:
            try:
                ticket = ticket_manager.create_ticket(
                    employee_name="System Monitor (Auto)",
                    department="IT",
                    issue_description=alert["description"],
                    category=alert["category"],
                    ticket_type="Incident",
                    impact="High"
                )
                created.append(ticket)
                log_event("CRITICAL",
                    f"Auto-ticket {ticket.ticket_id} for {alert['metric']} breach "
                    f"({alert['value']})")
            except Exception as e:
                log_event("ERROR", f"Auto-ticket creation failed: {e}")
        return created

    def run_full_check(self, ticket_manager) -> tuple:
        """Full cycle: collect → check → auto-ticket."""
        stats   = self.get_system_stats()
        alerts  = list(self.alert_generator(stats))   # use generator
        created = self.auto_create_tickets(alerts, ticket_manager) if alerts else []
        return stats, alerts, created

    # Display
    @staticmethod
    def display_stats(stats: dict):
        if not stats:
            print("  Could not retrieve system stats.")
            return

        print_header("System Health Monitor")
        print(f"  Checked At    : {stats['timestamp'][:19]}")
        print_separator()

        cpu = stats['cpu_percent']
        print(f"  CPU Usage     : {ascii_bar(cpu)}")
        if cpu > THRESHOLDS["cpu_percent"]:
            print(f"    *** ALERT: CPU exceeds {THRESHOLDS['cpu_percent']}%! ***")

        ram = stats['ram_percent']
        print(f"  RAM Usage     : {ascii_bar(ram)}")
        print(f"    Used: {stats['ram_used_gb']} GB / {stats['ram_total_gb']} GB")
        if ram > THRESHOLDS["ram_percent"]:
            print(f"    *** ALERT: RAM exceeds {THRESHOLDS['ram_percent']}%! ***")

        disk_used = stats['disk_used_percent']
        disk_free = stats['disk_free_percent']
        print(f"  Disk Usage    : {ascii_bar(disk_used)}")
        print(f"    Used: {stats['disk_used_gb']} GB / {stats['disk_total_gb']} GB"
              f"  Free: {stats['disk_free_gb']} GB")
        if disk_free < THRESHOLDS["disk_free_percent"]:
            print(f"    *** ALERT: Disk free below {THRESHOLDS['disk_free_percent']}%! ***")

        print(f"  Network Sent  : {stats['net_bytes_sent_mb']} MB  "
              f"Recv: {stats['net_bytes_recv_mb']} MB")
        print(f"  Packets Sent  : {stats['net_packets_sent']}  "
              f"Recv: {stats['net_packets_recv']}")
        print_separator()

    def display_alerts(self, alerts: list[dict]):
        if not alerts:
            print("\n  All systems healthy. No threshold alerts.")
            return
        print(f"\n  *** {len(alerts)} THRESHOLD ALERT(S) DETECTED ***")
        for a in alerts:
            print(f"    [{a['metric'].upper()}] {a['description']}")

    # History stats using map / filter
    def avg_cpu_from_history(self) -> float:
        if not self.__history:
            return 0.0
        cpu_values = list(map(lambda s: s["cpu_percent"], self.__history))
        return round(sum(cpu_values) / len(cpu_values), 2)

    def high_cpu_snapshots(self, threshold: float = 80.0) -> list[dict]:
        """filter() – return snapshots where CPU was above threshold."""
        return list(filter(lambda s: s["cpu_percent"] > threshold, self.__history))