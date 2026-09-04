import os
import sys
import json

def test_phase5_e2e():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base_dir)

    from src.alert_processor import AlertProcessor
    from src.incident_engine import IncidentEngine
    from src.priority_engine import PriorityEngine
    from src.retriever import Retriever
    from src.reasoning import ReasoningEngine
    from src.models import Incident, Runbook
    
    data_dir = os.path.join(base_dir, "data")
    runbooks_dir = os.path.join(data_dir, "runbooks")
    
    with open(os.path.join(data_dir, "alerts.json"), "r") as f:
        raw_alerts = json.load(f)

    # 1. Deterministic Processing
    processor = AlertProcessor()
    alerts = processor.process_raw_alerts(raw_alerts)
    
    # 2. Duplicate detection check (started with 7, expect 6 after deduping ALT-004/ALT-005)
    assert len(alerts) == 6, f"Duplicate detection failed. Expected 6, got {len(alerts)}"
    
    # 3. Grouping & Noise Isolation
    incident_engine = IncidentEngine(data_dir)
    incidents, noise = incident_engine.group_alerts(alerts)
    
    # 4. Noise alerts check
    assert len(noise) == 1, "Noise alert isolation failed."
    assert noise[0].alert_id == "ALT-001", "Wrong noise alert isolated."

    # Priority Engine
    priority_engine = PriorityEngine()
    for inc in incidents:
        priority_engine.calculate_priority(inc)
        
    assert len(incidents) == 2, "Incident correlation failed."
    
    # Identify the incidents
    cascading_inc = next(i for i in incidents if "RTR-CORE-01" in i.affected_devices)
    unsupported_inc = next(i for i in incidents if "FW-EDGE-01" in i.affected_devices)

    # 5. Normal/Correlated Incident Check
    assert len(cascading_inc.alerts) == 3, "Cascading incident correlation failed."
    assert cascading_inc.priority == "P1", "Priority escalation failed."

    # 6. Unsupported incident check
    assert len(unsupported_inc.alerts) == 2, "Unsupported incident correlation failed."

    # LLM Reasoning setup
    retriever = Retriever(runbooks_dir)
    retriever.build_index()
    reasoning_engine = ReasoningEngine()

    # Normal Incident RAG
    symptoms_normal = " ".join([a.message for a in cascading_inc.alerts])
    rb_normal = retriever.retrieve(symptoms_normal)
    assert rb_normal and "RB-001" in rb_normal.runbook_id, "Retriever failed on normal incident."

    rec_normal = reasoning_engine.generate_recommendation(cascading_inc, rb_normal)
    
    # Unsupported Incident RAG (Should escalate rule-based or from LLM)
    symptoms_unsupported = " ".join([a.message for a in unsupported_inc.alerts])
    rb_unsupported = retriever.retrieve(symptoms_unsupported)
    rec_unsupported = reasoning_engine.generate_recommendation(unsupported_inc, rb_unsupported)
    assert rec_unsupported.requires_escalation is True, "Unsupported incident failed to escalate."

    # 7. Gemini Failure Check
    # We simulate a failure by breaking the API key temporarily
    old_key = reasoning_engine.gemini.api_key
    reasoning_engine.gemini.client = None
    
    # Create a dummy P3 incident that won't trigger deterministic escalation
    from src.models import AlertSeverity, Alert
    dummy_inc = Incident(
        incident_id="INC-DUMMY",
        created_at="2026-09-04T10:05:00Z",
        status="OPEN",
        priority="P3",
        alerts=[Alert(alert_id="A99", timestamp="T", device_id="D1", alert_type="unknown", severity=AlertSeverity.MEDIUM, message="Test")],
        affected_devices=["D1"]
    )
    
    rec_failure = reasoning_engine.generate_recommendation(dummy_inc, rb_normal)
    assert rec_failure.requires_escalation is True, "Gemini failure did not escalate."
    assert rec_failure.confidence == 0.0, "Gemini failure confidence not 0."
    assert "AI reasoning unavailable" in rec_failure.recommended_action, "Graceful fallback message missing."

    print("Phase 5 complete E2E testing passed! All 6 conditions verified.")

if __name__ == "__main__":
    test_phase5_e2e()
