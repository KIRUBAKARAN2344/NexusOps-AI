import json
from .models import Incident, Runbook, Recommendation
from .gemini_service import GeminiService
from .escalation import evaluate_escalation_rules

SYSTEM_PROMPT = """You are a Tier-1 Network Operations Assistant.
Your task is to review the network incident and a provided runbook to recommend a course of action.

HARD CONSTRAINTS:
1. ONLY base your recommendation on the provided runbook. Do not invent troubleshooting steps.
2. If the runbook DOES NOT clearly cover the incident symptoms, set requires_escalation to true and explain why.
3. Always include specific alert IDs and runbook sections in evidence_citations.
4. Your output MUST be in valid JSON format matching this schema:
{
  "recommended_action": "string (the specific action to take from the runbook)",
  "confidence": "float (0.0 to 1.0)",
  "evidence_citations": ["string (exact runbook clauses OR specific alert IDs that support this recommendation)"],
  "requires_escalation": "boolean (true if not covered by runbook or if runbook explicitly says to escalate)",
  "escalation_reason": "string or null"
}
"""

def _alert_evidence(incident: Incident) -> list:
    """Build a list of alert evidence strings from an incident's alerts."""
    return [
        f"Alert {a.alert_id}: [{a.severity}] {a.alert_type} on {a.device_id} — {a.message}"
        for a in incident.alerts
    ]


class ReasoningEngine:
    def __init__(self):
        self.gemini = GeminiService()

    def generate_recommendation(self, incident: Incident, runbook: Runbook) -> Recommendation:
        # Pre-check for deterministic escalation before wasting tokens.
        # Only fires for alert types that are inherently outside runbook scope.
        reason = evaluate_escalation_rules(incident)
        if reason:
            return Recommendation(
                incident_id=incident.incident_id,
                recommended_action=(
                    "Rule-based escalation: Immediately notify Tier-2/Tier-3 operations. "
                    "Do not attempt automated remediation for this alert type."
                ),
                confidence=1.0,
                # Always include the triggering alerts as evidence — never show empty citations
                evidence_citations=_alert_evidence(incident),
                runbook_id=runbook.runbook_id if runbook else None,
                requires_escalation=True,
                escalation_reason=reason
            )

        if not runbook:
            return Recommendation(
                incident_id=incident.incident_id,
                recommended_action="Escalate to Human. No matching runbook found for these symptoms.",
                confidence=1.0,
                evidence_citations=_alert_evidence(incident),
                runbook_id=None,
                requires_escalation=True,
                escalation_reason="No runbook covered this incident."
            )

        # Build prompt context
        alerts_context = json.dumps([a.model_dump() for a in incident.alerts], indent=2)
        
        prompt = f"""
        INCIDENT ALERTS:
        {alerts_context}
        
        AVAILABLE RUNBOOK:
        {runbook.title} ({runbook.runbook_id})
        {runbook.content}
        
        Please provide your JSON recommendation based on the system instructions.
        """

        try:
            response_text = self.gemini.get_structured_recommendation(prompt, SYSTEM_PROMPT)
            data = json.loads(response_text)
            
            return Recommendation(
                incident_id=incident.incident_id,
                recommended_action=data.get("recommended_action", "Error processing recommendation"),
                confidence=float(data.get("confidence", 0.0)),
                evidence_citations=data.get("evidence_citations", []),
                runbook_id=runbook.runbook_id,
                requires_escalation=data.get("requires_escalation", False),
                escalation_reason=data.get("escalation_reason")
            )
        except Exception as e:
            # Fallback if Gemini fails or API key is missing
            return Recommendation(
                incident_id=incident.incident_id,
                recommended_action="AI reasoning unavailable. Please manually review the attached runbook.",
                confidence=0.0,
                evidence_citations=_alert_evidence(incident),
                runbook_id=runbook.runbook_id,
                requires_escalation=True,
                escalation_reason=f"AI Service Error: {str(e)}"
            )
