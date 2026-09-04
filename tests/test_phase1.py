import os
import json
import sys

def test_data_generation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    # Check if files exist
    assert os.path.exists(os.path.join(data_dir, "alerts.json")), "alerts.json missing"
    assert os.path.exists(os.path.join(data_dir, "devices.json")), "devices.json missing"
    assert os.path.exists(os.path.join(data_dir, "links.json")), "links.json missing"
    assert os.path.exists(os.path.join(data_dir, "runbooks", "RB-001.md")), "RB-001.md missing"
    
    # Check loading data using models
    sys.path.append(base_dir)
    from src.models import Alert
    
    with open(os.path.join(data_dir, "alerts.json"), "r") as f:
        alerts_data = json.load(f)
        
    alerts = [Alert(**a) for a in alerts_data]
    assert len(alerts) > 0, "No alerts loaded"
    assert alerts[0].alert_id == "ALT-001", "Alert ID mismatch"
    
    print("Phase 1 tests passed successfully!")

if __name__ == "__main__":
    test_data_generation()
