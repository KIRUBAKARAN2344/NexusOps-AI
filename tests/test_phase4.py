import os
import sys

def test_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base_dir)
    
    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)
    
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    # Test analyze endpoint
    response = client.post("/api/analyze")
    assert response.status_code == 200
    data = response.json()
    
    assert "incidents" in data
    assert "noise_alerts" in data
    
    incidents = data["incidents"]
    assert len(incidents) > 0, "No incidents generated"
    
    print("Phase 4 and 5 (E2E API) tests passed successfully!")

if __name__ == "__main__":
    # Test client will only work if we install httpx
    # For now, just a basic import check
    import app
    print("App imported successfully without syntax errors.")
