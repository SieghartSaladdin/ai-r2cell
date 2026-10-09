from typing import Callable, List

# Registry of callbacks for real-time graph events
_callbacks: List[Callable[[dict], None]] = []

def register_callback(callback: Callable[[dict], None]) -> None:
    """Register a callback function to handle graph events."""
    _callbacks.append(callback)

def send_graph_event(node: str, status: str, thread_id: str) -> None:
    """
    Broadcasts a graph execution event to all registered listeners.
    Safe to call from worker threads.
    """
    message = {
        "event": "node_execution",
        "node": node,
        "status": status,
        "thread_id": thread_id
    }
    for callback in _callbacks:
        try:
            callback(message)
        except Exception as e:
            print(f"[EventBus] Error in callback: {e}")
