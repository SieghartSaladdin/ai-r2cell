import asyncio
import os
import shutil
import httpx
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.widgets import Header, Footer, Button, RichLog, TabbedContent, TabPane
from textual.reactive import reactive

# Import sub-modules (memecah logic)
from .widgets import QRDisplay, StatusBox

class DashboardApp(App):
    """TUI Dashboard for controlling FastAPI and Baileys Node.js."""

    CSS_PATH = "theme.tcss"
    # Merubah Header Aplikasi
    TITLE = "🎮 R2CELL"
    SUB_TITLE = "RETRO SYSTEM GATEWAY"

    BINDINGS = [
        ("q", "quit_app", "Quit System"),
        ("r", "restart_services", "Restart All"),
    ]

    # Reactive variables
    fastapi_status = reactive("Starting...")
    baileys_status = reactive("WAITING...")
    wa_phone = reactive("None")
    qr_data = reactive("")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Horizontal(id="main-split"):
            # Menggunakan VerticalScroll agar tidak hancur saat layar terlalu resize/kecil
            with VerticalScroll(id="left-panel"):
                yield StatusBox("[b]SYSTEM STATUS[/b]", classes="main-status")
                yield StatusBox(id="fastapi-status")
                yield StatusBox(id="baileys-status")
                
                yield QRDisplay("WAITING FOR SIGNAL...", id="qr-container")
                
                yield Button("⚡ PING CONNECTION", id="btn-test")
                yield Button("☢️ EMERGENCY RESET", id="btn-reset")

            # Right Panel: Logs
            with Vertical(id="right-panel"):
                with TabbedContent():
                    with TabPane("FastAPI Logs", id="tab-fastapi"):
                        yield RichLog(id="log-fastapi", classes="log-viewer", highlight=True, wrap=True)
                    with TabPane("Baileys Logs", id="tab-baileys"):
                        yield RichLog(id="log-baileys", classes="log-viewer", highlight=True, wrap=True)
                        
        yield Footer()

    async def on_mount(self) -> None:
        self.log_fastapi = self.query_one("#log-fastapi", RichLog)
        self.log_baileys = self.query_one("#log-baileys", RichLog)
        
        self.fastapi_process = None
        self.node_process = None
        
        self.start_fastapi()
        self.start_baileys()

        self.set_interval(1.0, self.poll_status)

    def start_fastapi(self):
        self.fastapi_status = "BOOTING..."
        python_exe = os.path.join("venv", "Scripts", "python.exe")
        cmd = f"\"{python_exe}\" -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --log-level warning"
        self.run_worker(self.stream_subprocess(cmd, self.log_fastapi, tag="FastAPI"), exclusive=False)

    def start_baileys(self):
        self.baileys_status = "INITIALIZING..."
        node_script = os.path.join("src", "integrations", "whatsapp", "whatsapp.js")
        cmd = f"node \"{node_script}\""
        self.run_worker(self.stream_subprocess(cmd, self.log_baileys, tag="Baileys"), exclusive=False)

    async def stream_subprocess(self, command: str, log_widget: RichLog, tag: str):
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        if tag == "FastAPI":
            self.fastapi_process = process
            self.fastapi_status = f"RUNNING (PID: {process.pid})"
        elif tag == "Baileys":
            self.node_process = process
            
        async for line in process.stdout:
            line_str = line.decode('utf-8', errors='replace').rstrip()
            if line_str:
                log_widget.write(f"[{tag}] {line_str}")
                
        await process.wait()
        log_widget.write(f"[{tag}] PROCESS TERMINATED.")
        
        if tag == "FastAPI":
            self.fastapi_status = "OFFLINE"

    async def poll_status(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("http://127.0.0.1:8000/api/internal/status", timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.fastapi_status = f"ONLINE [green]OK[/green]"
                    b_state = data.get("baileys", {})
                    
                    self.baileys_status = b_state.get("state", "UNKNOWN")
                    self.qr_data = b_state.get("qr", "")
                    self.wa_phone = b_state.get("phone", "None")
        except BaseException:
            self.fastapi_status = f"[red]API UNREACHABLE[/red]"

    def watch_fastapi_status(self, new_val: str):
        try:
            self.query_one("#fastapi-status", StatusBox).update(f"[b]FASTAPI CORE:[/b]\n{new_val}")
        except: pass

    def watch_baileys_status(self, new_val: str):
        try:
            color = "#00ff00" if new_val == "CONNECTED" else "#ff0000" if new_val == "DISCONNECTED" else "#ffff00"
            self.query_one("#baileys-status", StatusBox).update(
                f"[b]NODE MODULE:[/b]\n[{color}]{new_val}[/{color}]\n[b]PHONE:[/b] {self.wa_phone}"
            )
        except: pass
            
    def watch_wa_phone(self, new_val: str):
        self.watch_baileys_status(self.baileys_status)

    def watch_qr_data(self, new_val: str):
        try:
            self.query_one("#qr-container", QRDisplay).update_qr(new_val)
        except: pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-test":
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("http://127.0.0.1:8000/")
                    if resp.status_code == 200:
                        event.button.label = "⚡ SUCCESS"
                    else:
                        event.button.label = "⚡ FAILED"
            except:
                event.button.label = "⚡ ERROR"
                
            await asyncio.sleep(2)
            event.button.label = "⚡ PING CONNECTION"

        elif event.button.id == "btn-reset":
            await self.action_reset_session()

    async def action_reset_session(self):
        if self.node_process:
            try:
                self.log_baileys.write(">>> DEPLOYING FORCE KILL TO NODE PROCESS...")
                self.node_process.kill()
                await self.node_process.wait()
            except: pass
        
        auth_dir = os.path.join("src", "integrations", "whatsapp", "auth_info_baileys")
        if os.path.exists(auth_dir):
            try:
                shutil.rmtree(auth_dir)
                self.log_baileys.write(f">>> DELETED AUTH FOLDER: {auth_dir}")
            except Exception as e:
                self.log_baileys.write(f">>> ERRROR PURGING FOLDER: {e}")
                
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://127.0.0.1:8000/api/internal/status", json={"state": "RESETTING", "qr": "", "phone": ""})
        except: pass
                
        self.start_baileys()

    async def action_restart_services(self) -> None:
        if self.fastapi_process:
            try: self.fastapi_process.kill()
            except: pass
        if self.node_process:
            try: self.node_process.kill()
            except: pass
        self.log_fastapi.clear()
        self.log_baileys.clear()
        self.start_fastapi()
        self.start_baileys()

    async def action_quit_app(self) -> None:
        if self.fastapi_process:
            try: self.fastapi_process.kill()
            except: pass
        if self.node_process:
            try: self.node_process.kill()
            except: pass
        self.exit()
