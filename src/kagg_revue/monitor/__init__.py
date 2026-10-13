"""Local training and model-performance monitoring."""

from kagg_revue.monitor.app import create_app
from kagg_revue.monitor.config import MonitorSettings

__all__ = ["MonitorSettings", "create_app"]
