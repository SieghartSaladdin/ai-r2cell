import asyncio
import os
import sys
import shutil
import time
import httpx
import webbrowser
import signal
import subprocess

from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import ANSI

from rich.console import Console
from rich.text import Text

from .menu import render_menu
from .statusbar import render_status_bar
from .logview import tail_log_file


class DashboardApp:
    """R2CELL Services Gateway TUI — prompt_toolkit + Rich."""

    def __init__(self):
        # Service metrics
        self.api_metrics = {"request_count": 0, "last_request": "never"}
        self.wa_metrics = {"uptime": 0, "message_count": 0, "error": "", "pid": 0}
        self.frontend_metrics = {"active_connections": 0}

        self.statuses = {"FastAPI": "offline", "Baileys": "offline", "Frontend": "offline"}
        self.uptimes = {"FastAPI": 0, "Baileys": 0, "Frontend": 0}
        self.procs = {"FastAPI": None, "Baileys": None, "Frontend": None}

        # Menu
        self.menu_options = [
            "Start All Services",
            "Stop All Services",
            "Restart All Services",
            "──",
            "View Logs",
            "Open QR Page",
            "Reset WhatsApp Session",
            "──",
            "Quit",
        ]
        self.log_menu_options = [
            "FastAPI Backend",
            "WhatsApp Gateway",
            "Web Dashboard",
            "──",
            "Back",
        ]

        # UI state
        self.current_view = "menu"       # menu | logs_menu | logs | confirm_quit | confirm_reset | resetting
        self.selected_index = 0
        self.last_baileys_state = "DISCONNECTED"
        self.status_message = ""         # ephemeral action feedback
        self.status_message_until = 0.0  # timestamp when to clear it

        # Disconnect warning
        self.disconnect_warning = False
        self.warning_cycle = 0
        self.flash_warning_task = None

        # Logs
        self.log_lines = []
        self.current_log_service = None
        self.tail_task = None

        # Rich & prompt_toolkit
        self.console = Console(force_terminal=True, color_system="truecolor")
        self.polling_task = None
        self.uptime_task = None
        self.pt_app = None

        self._setup_layout()
        self._setup_keybindings()

    # ── Layout ────────────────────────────────────────

    def _setup_layout(self):
        self.header_control = FormattedTextControl(self._render_header)
        self.body_control = FormattedTextControl(self._render_body)

        self.layout_container = HSplit([
            Window(content=self.header_control, height=4),
            Window(content=self.body_control),
        ])

    # ── Keybindings ───────────────────────────────────

    def _setup_keybindings(self):
        self.kb = KeyBindings()

        @self.kb.add("up")
        def _(event):
            self._move(-1)

        @self.kb.add("down")
        def _(event):
            self._move(1)

        @self.kb.add("enter")
        def _(event):
            self._select()

        @self.kb.add("escape")
        def _(event):
            if self.current_view == "logs":
                self._stop_log()
            elif self.current_view == "logs_menu":
                self.current_view = "menu"
                self.selected_index = 4
            elif self.current_view in ("confirm_quit", "confirm_reset"):
                self._back()

        @self.kb.add("q")
        def _(event):
            if self.current_view in ("menu", "logs_menu"):
                self.current_view = "confirm_quit"
            elif self.current_view == "logs":
                self._stop_log()
            elif self.current_view in ("confirm_quit", "confirm_reset"):
                self._back()

        @self.kb.add("1")
        def _(event):
            if self.current_view in ("menu", "logs_menu"):
                self._start_log("FastAPI")

        @self.kb.add("2")
        def _(event):
            if self.current_view in ("menu", "logs_menu"):
                self._start_log("Baileys")

        @self.kb.add("3")
        def _(event):
            if self.current_view in ("menu", "logs_menu"):
                self._start_log("Frontend")

        @self.kb.add("y")
        def _(event):
            if self.current_view == "confirm_quit":
                self.pt_app.exit()
            elif self.current_view == "confirm_reset":
                asyncio.create_task(self._reset_wa())

        @self.kb.add("n")
        def _(event):
            if self.current_view in ("confirm_quit", "confirm_reset"):
                self._back()

    # ── Entrypoint ────────────────────────────────────

    def run(self):
        asyncio.run(self._main())

    async def _main(self):
        # Clear old logs
        for tag in ("FastAPI", "Baileys", "Frontend"):
            path = f"logs/{tag.lower()}.log"
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

        self._start_all()

        self.polling_task = asyncio.create_task(self._poll_loop())
        self.uptime_task = asyncio.create_task(self._uptime_loop())

        try:
            from prompt_toolkit.output.defaults import create_output
            output = create_output()
        except Exception:
            from prompt_toolkit.output import DummyOutput
            output = DummyOutput()

        self.pt_app = Application(
            layout=Layout(self.layout_container),
            key_bindings=self.kb,
            full_screen=True,
            output=output,
        )

        try:
            await self.pt_app.run_async()
        finally:
            self.polling_task.cancel()
            self.uptime_task.cancel()
            if self.tail_task:
                self.tail_task.cancel()
            if self.flash_warning_task:
                self.flash_warning_task.cancel()
            await self._cleanup()

    # ── Rendering ─────────────────────────────────────

    def _rich_to_ansi(self, renderable) -> ANSI:
        with self.console.capture() as cap:
            self.console.print(renderable, highlight=False)
        return ANSI(cap.get())

    def _render_header(self) -> ANSI:
        bar = render_status_bar(
            api_metrics=self.api_metrics,
            wa_metrics=self.wa_metrics,
            web_metrics=self.frontend_metrics,
            statuses=self.statuses,
            uptimes=self.uptimes,
            disconnect_warning=self.disconnect_warning,
            warning_cycle=self.warning_cycle,
        )
        return self._rich_to_ansi(bar)

    def _render_body(self) -> ANSI:
        body = Text()

        if self.current_view == "menu":
            body = render_menu(self.menu_options, self.selected_index)
            # Append ephemeral status message
            if self.status_message and time.time() < self.status_message_until:
                body.append(f"\n  {self.status_message}\n", style="bold #10b981")
            elif self.status_message:
                self.status_message = ""

        elif self.current_view == "logs_menu":
            body = render_menu(self.log_menu_options, self.selected_index)

        elif self.current_view == "logs":
            body.append(f"\n  {self.current_log_service} Logs", style="bold #7c8aff")
            body.append("  (Esc to go back)\n\n", style="dim #555566")
            for line in self.log_lines:
                body.append("  ").append(line).append("\n")
            if not self.log_lines:
                body.append("  waiting for output…\n", style="dim #555566")

        elif self.current_view == "confirm_quit":
            body.append("\n  Quit R2CELL? ", style="bold #c8ccd4")
            body.append("[y/n]\n", style="dim #888899")

        elif self.current_view == "confirm_reset":
            body.append("\n  ⚠  This wipes WhatsApp auth and requires a fresh QR scan.\n", style="#f59e0b")
            body.append("  Continue? ", style="bold #c8ccd4")
            body.append("[y/n]\n", style="dim #888899")

        elif self.current_view == "resetting":
            body.append("\n  Resetting… waiting for new QR.\n", style="#10b981")

        return self._rich_to_ansi(body)

    # ── Menu Navigation ───────────────────────────────

    def _move(self, offset: int):
        if self.current_view not in ("menu", "logs_menu"):
            return
        opts = self.menu_options if self.current_view == "menu" else self.log_menu_options
        n = len(opts)
        for _ in range(n):
            self.selected_index = (self.selected_index + offset) % n
            if not opts[self.selected_index].startswith("──"):
                break
        if self.pt_app:
            self.pt_app.invalidate()

    def _back(self):
        self.current_view = "menu"
        self.selected_index = 0
        if self.pt_app:
            self.pt_app.invalidate()

    def _select(self):
        if self.current_view == "menu":
            opt = self.menu_options[self.selected_index]
            if opt == "Start All Services":
                self._start_all()
                self._flash("✓ Services starting")
            elif opt == "Stop All Services":
                self._stop_all()
                self._flash("✓ Services stopped")
            elif opt == "Restart All Services":
                self._restart_all()
                self._flash("✓ Services restarting")
            elif opt == "View Logs":
                self.current_view = "logs_menu"
                self.selected_index = 0
            elif opt == "Open QR Page":
                webbrowser.open("http://localhost:8000/qr")
                self._flash("✓ Opened in browser")
            elif opt == "Reset WhatsApp Session":
                self.current_view = "confirm_reset"
            elif opt == "Quit":
                self.current_view = "confirm_quit"

        elif self.current_view == "logs_menu":
            opt = self.log_menu_options[self.selected_index]
            if opt == "FastAPI Backend":
                self._start_log("FastAPI")
            elif opt == "WhatsApp Gateway":
                self._start_log("Baileys")
            elif opt == "Web Dashboard":
                self._start_log("Frontend")
            elif opt == "Back":
                self.current_view = "menu"
                self.selected_index = 4

        if self.pt_app:
            self.pt_app.invalidate()

    def _flash(self, msg: str, duration: float = 2.0):
        """Show an ephemeral status message below the menu."""
        self.status_message = msg
        self.status_message_until = time.time() + duration

    # ── Log Streaming ─────────────────────────────────

    def _start_log(self, service: str):
        if self.tail_task:
            self.tail_task.cancel()
        self.current_view = "logs"
        self.current_log_service = service
        self.log_lines = []
        self.tail_task = asyncio.create_task(
            tail_log_file(f"logs/{service.lower()}.log", self._on_log_lines)
        )
        if self.pt_app:
            self.pt_app.invalidate()

    def _stop_log(self):
        if self.tail_task:
            self.tail_task.cancel()
            self.tail_task = None
        self.current_view = "logs_menu"
        self.selected_index = 0
        self.log_lines = []
        if self.pt_app:
            self.pt_app.invalidate()

    def _on_log_lines(self, lines: list, reset: bool = False):
        if reset:
            self.log_lines = lines
        else:
            self.log_lines.extend(lines)
            if len(self.log_lines) > 50:
                self.log_lines = self.log_lines[-50:]
        if self.current_view == "logs" and self.pt_app:
            self.pt_app.invalidate()

    # ── Process Management ────────────────────────────

    def _cmd(self, tag: str) -> tuple[str, str | None]:
        if tag == "FastAPI":
            return f"\"{sys.executable}\" -u -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level info", None
        if tag == "Baileys":
            return f"node \"{os.path.join('src', 'integrations', 'whatsapp', 'whatsapp.js')}\"", None
        if tag == "Frontend":
            return "npm run dev", "admin-dashboard"
        return "echo noop", None

    def _launch(self, tag: str):
        self.statuses[tag] = "booting"
        self.uptimes[tag] = 0
        cmd, cwd = self._cmd(tag)

        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{tag.lower()}.log", "a", encoding="utf-8") as f:
            f.write(f"▸ starting: {cmd}\n")

        asyncio.create_task(self._stream(cmd, tag, cwd))

    async def _stream(self, command: str, tag: str, cwd: str | None = None):
        log_file = f"logs/{tag.lower()}.log"
        env = os.environ.copy()
        env["R2CELL_TUI"] = "true"

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
                cwd=cwd,
            )
            self.procs[tag] = proc
            self.statuses[tag] = "running"
            self.uptimes[tag] = time.time()
            if self.pt_app:
                self.pt_app.invalidate()

            with open(log_file, "a", encoding="utf-8", errors="replace") as f:
                async for raw in proc.stdout:
                    line = raw.decode("utf-8", errors="replace")
                    # Filter internal polling noise
                    if any(k in line for k in ("/api/internal/status", "/wa/status", "/logs/")):
                        continue
                    f.write(line)
                    f.flush()

            await proc.wait()
        except Exception as e:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"✗ error: {e}\n")

        self.procs[tag] = None
        self.statuses[tag] = "offline"
        self.uptimes[tag] = 0
        if self.pt_app:
            self.pt_app.invalidate()

    def _kill(self, tag: str):
        proc = self.procs.get(tag)
        if proc:
            self._kill_tree(proc)
            self.procs[tag] = None
        self.statuses[tag] = "offline"
        self.uptimes[tag] = 0

    def _kill_tree(self, proc):
        if not proc:
            return
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                proc.kill()
        except Exception:
            pass

    def _kill_pid(self, pid: int):
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                os.kill(pid, signal.SIGKILL)
        except Exception:
            pass

    # ── Service Controls ──────────────────────────────

    def _start_all(self):
        for tag in ("FastAPI", "Baileys", "Frontend"):
            if not self.procs[tag]:
                self._launch(tag)

    def _stop_all(self):
        for tag in ("FastAPI", "Baileys", "Frontend"):
            self._kill(tag)
        wa_pid = self.wa_metrics.get("pid", 0)
        if wa_pid:
            self._kill_pid(wa_pid)
            asyncio.create_task(self._push_disconnected())

    def _restart_all(self):
        self._stop_all()
        self._start_all()

    async def _push_disconnected(self):
        try:
            async with httpx.AsyncClient() as c:
                await c.post(
                    "http://127.0.0.1:8000/api/internal/status",
                    json={"state": "DISCONNECTED", "qr": "", "phone": "", "pid": 0, "error": ""},
                )
        except Exception:
            pass

    async def _reset_wa(self):
        self.current_view = "resetting"
        if self.pt_app:
            self.pt_app.invalidate()

        self._kill("Baileys")

        try:
            async with httpx.AsyncClient() as c:
                await c.post("http://127.0.0.1:8000/wa/reset-session", timeout=10.0)
        except Exception:
            pass

        await asyncio.sleep(2.0)
        self._back()

    # ── Background Loops ──────────────────────────────

    async def _uptime_loop(self):
        """Refresh the header periodically so uptimes tick."""
        while True:
            await asyncio.sleep(2.0)
            if self.pt_app:
                self.pt_app.invalidate()

    async def _poll_loop(self):
        """Poll FastAPI internal status every 2 seconds."""
        await asyncio.sleep(2.0)

        while True:
            try:
                async with httpx.AsyncClient() as c:
                    r = await c.get("http://127.0.0.1:8000/api/internal/status", timeout=1.5)
                    if r.status_code == 200:
                        data = r.json()

                        # FastAPI
                        self.api_metrics = data.get("fastapi", {})
                        if self.procs.get("FastAPI"):
                            self.statuses["FastAPI"] = "online"
                        else:
                            self.statuses["FastAPI"] = "running"

                        # Baileys
                        baileys = data.get("baileys", {})
                        new_state = baileys.get("state", "DISCONNECTED").upper()

                        if self.last_baileys_state == "AUTHENTICATED" and new_state == "DISCONNECTED":
                            self.disconnect_warning = True
                            self.warning_cycle = 0
                            if self.flash_warning_task:
                                self.flash_warning_task.cancel()
                            self.flash_warning_task = asyncio.create_task(self._flash_warning())

                        if new_state in ("AUTHENTICATED", "CONNECTED", "CONNECTING", "QR_PENDING"):
                            self.disconnect_warning = False
                            if self.flash_warning_task:
                                self.flash_warning_task.cancel()
                                self.flash_warning_task = None

                        self.last_baileys_state = new_state
                        self.statuses["Baileys"] = new_state
                        self.wa_metrics = {
                            "uptime": baileys.get("uptime", 0),
                            "message_count": baileys.get("message_count", 0),
                            "error": baileys.get("error", ""),
                            "pid": baileys.get("pid", 0),
                        }

                        # Frontend
                        self.frontend_metrics = data.get("frontend", {})
                        if self.procs.get("Frontend"):
                            self.statuses["Frontend"] = "online"
                        else:
                            self.statuses["Frontend"] = "running"

            except Exception:
                if self.procs.get("FastAPI"):
                    self.statuses["FastAPI"] = "unreachable"
                else:
                    self.statuses["FastAPI"] = "offline"
                self.statuses["Baileys"] = "offline"
                self.statuses["Frontend"] = "offline"
                self.last_baileys_state = "DISCONNECTED"

            if self.pt_app:
                self.pt_app.invalidate()

            await asyncio.sleep(2.0)

    async def _flash_warning(self):
        try:
            while self.warning_cycle < 6:
                await asyncio.sleep(0.5)
                self.warning_cycle += 1
                if self.pt_app:
                    self.pt_app.invalidate()
        except asyncio.CancelledError:
            pass

    async def _cleanup(self):
        self._stop_all()
