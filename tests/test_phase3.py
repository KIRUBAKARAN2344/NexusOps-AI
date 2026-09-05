import os
import sys

def test_phase3():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base_dir)
    
    from src.retriever import Retriever
    from src.reasoning import ReasoningEngine
    from src.models import Incident, Alert, AlertSeverity

    data_dir = os.path.join(base_dir, "data")
    runbooks_dir = os.path.join(data_dir, "runbooks")
    
    # Test Retriever
    retriever = Retriever(runbooks_dir)
    retriever.build_index()
    
    assert len(retriever.runbooks) == 2, "Expected 2 runbooks loaded"
    
    # Try retrieving a runbook for link down
    rb = retriever.retrieve("interface GigabitEthernet0/1 to SW-DIST-01 is DOWN")
    assert rb is not None, "Failed to retrieve runbook"
    assert "RB-001" in rb.runbook_id, "Expected RB-001 for link down"

    # Test Escalation Rule & Reasoning Engine
    engine = ReasoningEngine()
    
    # Use anomaly_detected — this is the alert type that triggers deterministic
    # pre-escalation (security anomalies outside standard runbook scope).
    dummy_incident = Incident(
        incident_id="INC-TEST1",
        created_at="2026-09-04T10:05:00Z",
        priority="P2",
        alerts=[
            Alert(alert_id="A1", timestamp="T", device_id="FW-1", alert_type="anomaly_detected", severity=AlertSeverity.HIGH, message="Unknown encrypted traffic spike")
        ],
        affected_devices=["FW-1"]
    )
    
    # anomaly_detected HIGH triggers deterministic escalation before Gemini is called
    rec = engine.generate_recommendation(dummy_incident, rb)
    assert rec.requires_escalation is True
    assert "Deterministic Escalation" in rec.escalation_reason
    # Evidence must always be populated — never show empty citations
    assert len(rec.evidence_citations) > 0, "Evidence citations must not be empty for deterministic escalation"

    print("Phase 3 reasoning engine tests passed successfully!")

if __name__ == "__main__":
    test_phase3()
