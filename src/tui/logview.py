import os
import asyncio
from rich.text import Text


def parse_log_line(line: str) -> Text:
    """Color a log line by severity — keeps it simple."""
    s = line.rstrip()
    low = s.lower()

    if "error" in low or "fail" in low or "traceback" in low:
        return Text(s, style="#ef4444")
    if "warn" in low:
        return Text(s, style="#f59e0b")
    if "success" in low or "✓" in low:
        return Text(s, style="#10b981")
    return Text(s, style="#888899")


async def tail_log_file(filepath: str, update_callback, max_lines: int = 50):
    """
    Tail a log file. Shows last `max_lines` on open, then streams new lines.
    Calls `update_callback(lines, reset)` to push data to the UI.
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else "logs", exist_ok=True)

    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("— waiting for output —\n")

    # Initial read — show last N lines
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            tail = [parse_log_line(l) for l in all_lines[-max_lines:]]
            update_callback(tail, reset=True)
            last_pos = f.tell()
    except Exception as e:
        update_callback([Text(f"Failed to read: {e}", style="#ef4444")], reset=True)
        return

    # Tailing loop
    try:
        while True:
            try:
                size = os.path.getsize(filepath)
            except Exception:
                size = last_pos

            # File truncated
            if size < last_pos:
                update_callback([Text("— log cleared —", style="dim #555566")], reset=True)
                last_pos = 0

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(last_pos)
                    new = []
                    for raw in f:
                        if raw.strip():
                            new.append(parse_log_line(raw))
                    if new:
                        update_callback(new, reset=False)
                    last_pos = f.tell()
            except Exception:
                pass

            await asyncio.sleep(0.3)
    except asyncio.CancelledError:
        pass
