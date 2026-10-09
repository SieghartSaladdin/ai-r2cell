import time

class GatewayState:
    def __init__(self):
        self.state = "DISCONNECTED"
        self.qr = ""
        self.phone = ""
        self.pid = 0
        self.error = ""
        self.uptime_start = 0.0
        self.message_count = 0

    def to_dict(self):
        return {
            "state": self.state,
            "qr": self.qr,
            "phone": self.phone,
            "pid": self.pid,
            "error": self.error
        }

gateway_state = GatewayState()
