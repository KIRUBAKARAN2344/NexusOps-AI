from .models import Incident, AlertSeverity

class PriorityEngine:
    def calculate_priority(self, incident: Incident) -> None:
        """
        Deterministically calculates the priority of an incident (P1, P2, P3, P4).
        Updates the incident object in-place.
        """
        highest_severity = "INFO"
        severity_levels = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.HIGH: 3,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 1,
            AlertSeverity.INFO: 0
        }
        
        max_level = 0
        for alert in incident.alerts:
            level = severity_levels.get(alert.severity, 0)
            if level > max_level:
                max_level = level

        # Base Priority from Highest Severity
        if max_level == 4:
            incident.priority = "P1"
        elif max_level == 3:
            incident.priority = "P2"
        elif max_level == 2:
            incident.priority = "P3"
        else:
            incident.priority = "P4"

        # Escalation Rules: if multiple devices are affected, bump priority if not already P1
        if len(incident.affected_devices) >= 3 and incident.priority != "P1":
            if incident.priority == "P2":
                incident.priority = "P1"
            elif incident.priority == "P3":
                incident.priority = "P2"
            elif incident.priority == "P4":
                incident.priority = "P3"
