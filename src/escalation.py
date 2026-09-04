from typing import Optional
from .models import Incident, AlertSeverity

def evaluate_escalation_rules(incident: Incident) -> Optional[str]:
    """
    Deterministic rule-based escalation check BEFORE calling Gemini.
    Returns the reason for escalation if true, None otherwise.
    """
    if incident.priority == "P1":
        return "Deterministic Escalation: P1 incident affecting multiple devices requires immediate human oversight."
        
    for alert in incident.alerts:
        if alert.alert_type == "anomaly_detected" and alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return "Deterministic Escalation: High severity security anomaly detected. Cannot be auto-remediated."

    return None
