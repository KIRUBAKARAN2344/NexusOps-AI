from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class AlertSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class Alert(BaseModel):
    alert_id: str
    timestamp: str
    device_id: str
    alert_type: str  # e.g., "link_down", "device_unreachable", "high_latency"
    severity: AlertSeverity
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"

class Incident(BaseModel):
    incident_id: str
    created_at: str
    status: IncidentStatus = IncidentStatus.OPEN
    priority: str = "P3"
    alerts: List[Alert] = Field(default_factory=list)
    summary: str = ""
    affected_devices: List[str] = Field(default_factory=list)

class Runbook(BaseModel):
    runbook_id: str
    title: str
    content: str
    keywords: List[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    incident_id: str
    recommended_action: str
    confidence: float
    evidence_citations: List[str] = Field(default_factory=list)
    runbook_id: Optional[str] = None
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
