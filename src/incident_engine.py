from typing import List, Dict, Any
import json
import os
import uuid
from datetime import datetime
from .models import Alert, Incident, IncidentStatus

class IncidentEngine:
    def __init__(self, data_dir: str):
        self.links = self._load_json(os.path.join(data_dir, "links.json"))
        self.topology = self._build_topology()
        self.noise_threshold_severity = ["INFO", "LOW"]

    def _load_json(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            return json.load(f)

    def _build_topology(self) -> Dict[str, List[str]]:
        # Builds an undirected adjacency list
        graph = {}
        for link in self.links:
            s, t = link.get("source"), link.get("target")
            if s and t:
                graph.setdefault(s, []).append(t)
                graph.setdefault(t, []).append(s)
        return graph

    def group_alerts(self, alerts: List[Alert]) -> tuple[List[Incident], List[Alert]]:
        """
        Groups alerts into Incidents based on topology and time, isolating noise.
        Returns (incidents, noise_alerts).
        """
        incidents = []
        noise = []
        
        # Sort alerts chronologically
        try:
            alerts.sort(key=lambda x: datetime.fromisoformat(x.timestamp.replace('Z', '+00:00')))
        except ValueError:
            pass

        for alert in alerts:
            # Rule 1: Identify noise
            if alert.severity in self.noise_threshold_severity and alert.alert_type not in ["link_down", "device_unreachable"]:
                noise.append(alert)
                continue

            # Rule 2: Attempt to correlate with existing incidents
            correlated = False
            for incident in incidents:
                if self._is_correlated(incident, alert):
                    incident.alerts.append(alert)
                    if alert.device_id not in incident.affected_devices:
                        incident.affected_devices.append(alert.device_id)
                    correlated = True
                    break
            
            # Rule 3: Create a new incident if no correlation
            if not correlated:
                new_incident = Incident(
                    incident_id=f"INC-{uuid.uuid4().hex[:6].upper()}",
                    created_at=alert.timestamp,
                    status=IncidentStatus.OPEN,
                    alerts=[alert],
                    affected_devices=[alert.device_id]
                )
                incidents.append(new_incident)

        return incidents, noise

    def _is_correlated(self, incident: Incident, alert: Alert) -> bool:
        """
        Determine if an alert belongs to an incident.
        Correlation rules:
        - Same device
        - Devices are direct neighbors in topology
        """
        for inc_alert in incident.alerts:
            # Same device
            if inc_alert.device_id == alert.device_id:
                return True
            
            # Neighboring devices
            neighbors = self.topology.get(inc_alert.device_id, [])
            if alert.device_id in neighbors:
                return True
                
        return False
