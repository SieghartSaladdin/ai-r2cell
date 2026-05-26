import io
import qrcode
from textual.widgets import Static

def build_qr_string(data: str) -> str:
    """Konversi plain String URL ke blok ANSI Terminal."""
    if not data:
        return "[b]NO ACTIVE QR SIGNAL[/b]"
    try:
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(data)
        qr.make(fit=True)
        f = io.StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        return f.read()
    except Exception:
        return "[red]QR GENERATION ERROR[/red]"

class QRDisplay(Static):
    """Widget Khusus untuk merender QR."""
    def update_qr(self, data: str):
        self.update(build_qr_string(data))

class StatusBox(Static):
    """Widget panel sederhana."""
    pass
