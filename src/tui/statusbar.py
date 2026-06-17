import time
from rich.text import Text
from rich.table import Table


def _duration(start: float) -> str:
    """Human-readable duration from a start timestamp."""
    if start <= 0:
        return "—"
    s = int(time.time() - start)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"


def _dot(status: str) -> tuple[str, str]:
    """Returns (dot_char, color) for a service status string."""
    s = status.upper()
    if s in ("ONLINE", "RUNNING", "CONNECTED", "AUTHENTICATED"):
        return "●", "#10b981"
    if s in ("BOOTING", "CONNECTING", "QR_PENDING", "NEED SCAN"):
        return "●", "#f59e0b"
    if s in ("OFFLINE", "ERROR", "DISCONNECTED", "UNREACHABLE"):
        return "○", "#555566"
    return "○", "#555566"


# Service endpoint info
SERVICE_URLS = {
    "FastAPI": "http://localhost:8000",
    "Baileys": "http://localhost:8000/qr",
    "Frontend": "http://localhost:5173",
}


def render_status_bar(
    api_metrics: dict,
    wa_metrics: dict,
    web_metrics: dict,
    statuses: dict,
    uptimes: dict,
    disconnect_warning: bool = False,
    warning_cycle: int = 0,
) -> Table:
    """Render a compact 3-column status header with service URLs."""

    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)

    # ── Row 1: Status dots + uptime ───────────────────

    def _status_line(label: str, status: str, uptime_start: float, extra: str = "") -> Text:
        dot_char, color = _dot(status)
        t = Text()
        t.append(f"  {label}  ", style="bold #c8ccd4")
        t.append(f"{dot_char}", style=color)
        t.append(f" {status.lower()}", style=f"dim {color}")
        up = _duration(uptime_start)
        if up != "—":
            t.append(f"  ↑{up}", style="dim #555566")
        if extra:
            t.append(f"  {extra}", style="dim #555566")
        return t

    # ── Row 2: URL info ───────────────────────────────

    def _url_line(tag: str, status: str) -> Text:
        t = Text()
        url = SERVICE_URLS.get(tag, "")
        is_up = status.upper() in ("ONLINE", "RUNNING", "CONNECTED", "AUTHENTICATED", "BOOTING", "CONNECTING", "QR_PENDING", "NEED SCAN")
        if is_up and url:
            t.append(f"  └ {url}", style="dim #555566")
        else:
            t.append(f"  └ {url}", style="dim #333344")
        return t

    api_status = statuses.get("FastAPI", "offline")
    wa_status = statuses.get("Baileys", "offline")
    web_status = statuses.get("Frontend", "offline")

    # WhatsApp QR hint
    wa_extra = ""
    if wa_status.upper() in ("QR_PENDING", "NEED SCAN"):
        wa_extra = "scan QR!"

    col1 = _status_line("FastAPI", api_status, uptimes.get("FastAPI", 0))
    col2 = _status_line("WhatsApp", wa_status, uptimes.get("Baileys", 0), wa_extra)
    col3 = _status_line("Web", web_status, uptimes.get("Frontend", 0))

    url1 = _url_line("FastAPI", api_status)
    url2 = _url_line("Baileys", wa_status)
    url3 = _url_line("Frontend", web_status)

    grid.add_row(col1, col2, col3)
    grid.add_row(url1, url2, url3)

    # ── Wrap in outer container ───────────────────────
    outer = Table.grid(expand=True)
    outer.add_column()
    outer.add_row(grid)

    # Disconnect warning
    if disconnect_warning:
        style = "bold #ef4444" if warning_cycle % 2 == 0 and warning_cycle < 6 else "#ef4444"
        outer.add_row("")
        outer.add_row(Text("  ⚠  WhatsApp disconnected — visit http://localhost:8000/qr to reconnect", style=style))

    return outer

