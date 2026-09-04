import json
import os
from typing import List, Dict, Any
from datetime import datetime
from .models import Alert, AlertSeverity

class AlertProcessor:
    def __init__(self, dedup_window_seconds: int = 300):
        self.dedup_window_seconds = dedup_window_seconds
        
    def process_raw_alerts(self, raw_data: List[Dict[str, Any]]) -> List[Alert]:
        """Convert raw dicts to Alert models, handling validation."""
        alerts = []
        for raw in raw_data:
            try:
                alert = Alert(**raw)
                alerts.append(alert)
            except Exception as e:
                print(f"Skipping invalid alert data: {raw}, Error: {e}")
        return self.deduplicate_alerts(alerts)
        
    def deduplicate_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """
        Deduplicate alerts based on exact same type and device within a time window.
        Assumes alerts are roughly ordered by time.
        """
        unique_alerts = []
        seen = {}  # key: (device_id, alert_type), value: (timestamp_obj, alert_id)

        for alert in alerts:
            key = (alert.device_id, alert.alert_type)
            try:
                alert_time = datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Fallback if timestamp is unparseable, just keep the alert
                unique_alerts.append(alert)
                continue

            if key in seen:
                last_time, _ = seen[key]
                time_diff = (alert_time - last_time).total_seconds()
                if abs(time_diff) <= self.dedup_window_seconds:
                    # It's a duplicate, skip it
                    continue
            
            # Not a duplicate, update seen and add
            seen[key] = (alert_time, alert.alert_id)
            unique_alerts.append(alert)

        return unique_alerts
