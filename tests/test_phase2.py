import os
import json
import sys

def test_phase2():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base_dir)
    
    from src.alert_processor import AlertProcessor
    from src.incident_engine import IncidentEngine
    from src.priority_engine import PriorityEngine

    data_dir = os.path.join(base_dir, "data")
    
    with open(os.path.join(data_dir, "alerts.json"), "r") as f:
        raw_alerts = json.load(f)
        
    # Test AlertProcessor
    processor = AlertProcessor(dedup_window_seconds=300)
    alerts = processor.process_raw_alerts(raw_alerts)
    
    # We had 7 alerts, one was a duplicate
    assert len(alerts) == 6, f"Expected 6 deduped alerts, got {len(alerts)}"

    # Test IncidentEngine
    engine = IncidentEngine(data_dir)
    incidents, noise = engine.group_alerts(alerts)
    
    # Noise should be 1 (the cpu_util_high which is INFO)
    assert len(noise) == 1, f"Expected 1 noise alert, got {len(noise)}"
    assert noise[0].alert_id == "ALT-001"
    
    # We expect 2 incidents: 
    # 1. RTR-CORE-01 and SW-DIST-01 and SW-ACCESS-10 cascade
    # 2. FW-EDGE-01 alerts
    assert len(incidents) == 2, f"Expected 2 incidents, got {len(incidents)}"

    # Test PriorityEngine
    priority_engine = PriorityEngine()
    for incident in incidents:
        priority_engine.calculate_priority(incident)
    
    # The cascading one has CRITICAL alerts (P1)
    # The FW one has HIGH (P2)
    priorities = [i.priority for i in incidents]
    assert "P1" in priorities, "Expected at least one P1 incident"
    assert "P2" in priorities, "Expected at least one P2 incident"

    print("Phase 2 deterministic engine tests passed successfully!")

if __name__ == "__main__":
    test_phase2()
