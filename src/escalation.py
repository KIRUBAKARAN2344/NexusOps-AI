from typing import Optional
from .models import Incident, AlertSeverity

def evaluate_escalation_rules(incident: Incident) -> Optional[str]:
    """
    Deterministic rule-based escalation check BEFORE calling Gemini.
    Returns the escalation reason string if the incident must be escalated
    without calling the LLM, or None to allow Gemini + runbook to proceed.

    IMPORTANT: Priority (P1/P2/etc.) alone is NOT a reason to bypass Gemini.
    High-priority incidents that are covered by runbooks should receive a
    grounded recommendation, not a blanket rule-based escalation.
    Only escalate here when the alert type is inherently outside runbook scope.
    """
    for alert in incident.alerts:
        if alert.alert_type == "anomaly_detected" and alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
            return (
                "Deterministic Escalation: High-severity security anomaly detected "
                "(alert type 'anomaly_detected'). This pattern is outside standard "
                "runbook coverage and cannot be safely auto-remediated."
            )

    return None
