import os
import json
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from src.models import Alert, Incident
from src.alert_processor import AlertProcessor
from src.incident_engine import IncidentEngine
from src.priority_engine import PriorityEngine
from src.retriever import Retriever
from src.reasoning import ReasoningEngine

app = FastAPI(title="NexusOps AI - Incident Triage Assistant")

# Global state (for hackathon MVP simplicity)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RUNBOOKS_DIR = os.path.join(DATA_DIR, "runbooks")

# Initialize engines
retriever = Retriever(RUNBOOKS_DIR)
# Build index once on startup
retriever.build_index()

class AnalysisResponse(BaseModel):
    incidents: List[Dict[str, Any]]
    noise_alerts: List[Dict[str, Any]]

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "NexusOps AI is running"}

@app.get("/api/alerts")
async def get_raw_alerts():
    path = os.path.join(DATA_DIR, "alerts.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_alerts():
    """Run the end-to-end triage pipeline on the alerts.json file."""
    try:
        raw_alerts = await get_raw_alerts()
        
        # 1. Deterministic Processing
        processor = AlertProcessor()
        alerts = processor.process_raw_alerts(raw_alerts)
        
        # 2. Grouping & Noise Isolation
        incident_engine = IncidentEngine(DATA_DIR)
        incidents, noise = incident_engine.group_alerts(alerts)
        
        # 3. Priority Calculation
        priority_engine = PriorityEngine()
        for inc in incidents:
            priority_engine.calculate_priority(inc)
            
        # 4. LLM Reasoning (RAG)
        reasoning_engine = ReasoningEngine()
        results = []
        
        for inc in incidents:
            # Build an incident summary for search
            symptoms = " ".join([a.message for a in inc.alerts])
            search_query = f"device {inc.affected_devices[0]} symptoms: {symptoms}"
            
            runbook = retriever.retrieve(search_query)
            recommendation = reasoning_engine.generate_recommendation(inc, runbook)
            
            inc_dict = inc.model_dump()
            inc_dict["recommendation"] = recommendation.model_dump()
            results.append(inc_dict)

        return AnalysisResponse(
            incidents=results,
            noise_alerts=[a.model_dump() for a in noise]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/demo/{scenario}")
async def run_demo(scenario: str):
    """Placeholder for triggering specific demo flows."""
    return {"status": "ok", "scenario_triggered": scenario}

if os.path.exists("frontend") and os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
