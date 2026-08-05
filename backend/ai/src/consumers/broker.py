"""The taskiq worker entrypoint for inbound events.

The broker itself lives in registry.py so handler modules can import it
without importing this module back. Every handler module must be imported
here, or its task is never registered and its events sit unrouted.
"""

import src.consumers.ping  # noqa: F401
from src.consumers.registry import broker

__all__ = ["broker"]
