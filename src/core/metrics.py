import time

class MetricsState:
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0.0
        self.active_clients = {}  # client_ip -> last_seen_timestamp

metrics_state = MetricsState()
