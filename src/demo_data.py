import os
import json

def create_demo_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    runbooks_dir = os.path.join(data_dir, "runbooks")
    
    os.makedirs(runbooks_dir, exist_ok=True)
    
    devices = [
        {"device_id": "RTR-CORE-01", "type": "Router", "location": "Datacenter-A", "status": "active"},
        {"device_id": "SW-DIST-01", "type": "Switch", "location": "Datacenter-A", "status": "active"},
        {"device_id": "SW-ACCESS-10", "type": "Switch", "location": "Floor-1", "status": "active"},
        {"device_id": "FW-EDGE-01", "type": "Firewall", "location": "Datacenter-A", "status": "active"}
    ]
    
    links = [
        {"link_id": "LNK-001", "source": "RTR-CORE-01", "target": "SW-DIST-01", "capacity": "10G"},
        {"link_id": "LNK-002", "source": "SW-DIST-01", "target": "SW-ACCESS-10", "capacity": "1G"}
    ]
    
    # Generate some alerts based on scenarios
    alerts = [
        # Normal Routine Alert (Noise)
        {
            "alert_id": "ALT-001", "timestamp": "2026-09-04T10:00:00Z", "device_id": "SW-ACCESS-10",
            "alert_type": "cpu_util_high", "severity": "INFO", "message": "CPU utilization reached 75%",
            "metadata": {"cpu_val": 75}
        },
        # Cascading Failure (Incident 1 - Covered by Runbook)
        {
            "alert_id": "ALT-002", "timestamp": "2026-09-04T10:05:00Z", "device_id": "RTR-CORE-01",
            "alert_type": "link_down", "severity": "CRITICAL", "message": "Interface GigabitEthernet0/1 to SW-DIST-01 is DOWN",
            "metadata": {"interface": "GigabitEthernet0/1", "peer": "SW-DIST-01"}
        },
        {
            "alert_id": "ALT-003", "timestamp": "2026-09-04T10:05:01Z", "device_id": "SW-DIST-01",
            "alert_type": "bgp_neighbor_lost", "severity": "HIGH", "message": "BGP peer RTR-CORE-01 down",
            "metadata": {"peer": "RTR-CORE-01"}
        },
        {
            "alert_id": "ALT-004", "timestamp": "2026-09-04T10:05:05Z", "device_id": "SW-ACCESS-10",
            "alert_type": "device_unreachable", "severity": "CRITICAL", "message": "Device not responding to ping",
            "metadata": {}
        },
        # Duplicate Alert
        {
            "alert_id": "ALT-005", "timestamp": "2026-09-04T10:05:05Z", "device_id": "SW-ACCESS-10",
            "alert_type": "device_unreachable", "severity": "CRITICAL", "message": "Device not responding to ping",
            "metadata": {}
        },
        # Unsupported / Difficult Incident
        {
            "alert_id": "ALT-006", "timestamp": "2026-09-04T10:30:00Z", "device_id": "FW-EDGE-01",
            "alert_type": "anomaly_detected", "severity": "HIGH", "message": "Unknown encrypted traffic spike",
            "metadata": {"bytes": "50GB"}
        },
        {
            "alert_id": "ALT-007", "timestamp": "2026-09-04T10:30:05Z", "device_id": "FW-EDGE-01",
            "alert_type": "memory_leak_warning", "severity": "MEDIUM", "message": "Memory leaking in security module",
            "metadata": {}
        }
    ]
    
    with open(os.path.join(data_dir, "devices.json"), "w") as f:
        json.dump(devices, f, indent=2)
        
    with open(os.path.join(data_dir, "links.json"), "w") as f:
        json.dump(links, f, indent=2)
        
    with open(os.path.join(data_dir, "alerts.json"), "w") as f:
        json.dump(alerts, f, indent=2)
        
    # Create Runbooks
    rb1 = """# Runbook: Core Link Down Recovery (RB-001)

## Description
Procedure for handling physical link failures between Core Routers and Distribution Switches.

## Symptoms
- `link_down` alerts on Core interfaces
- `bgp_neighbor_lost` or routing protocol drops
- Downstream devices reporting `device_unreachable`

## Automated Triage
1. Identify the core interface that went down.
2. Check if a redundant path exists.
3. Verify if maintenance is scheduled.

## Recommended Action
If the link is DOWN and no maintenance is scheduled:
1. Verify physical connection / optics.
2. If BGP is down, gracefully shut the BGP neighbor to avoid flapping.
3. Reroute traffic to backup link.

## Escalation
If backup link is also saturated or down, escalate immediately to Tier 3 Network Engineering.
"""

    rb2 = """# Runbook: High CPU Utilization (RB-002)

## Description
Handling high CPU on access switches.

## Symptoms
- `cpu_util_high` alerts
- Occasional high latency pings

## Recommended Action
1. Check for spanning tree loops.
2. Verify if SNMP polling is causing the spike.
3. No immediate action needed if CPU is below 90% and stable.
"""

    with open(os.path.join(runbooks_dir, "RB-001.md"), "w") as f:
        f.write(rb1)
        
    with open(os.path.join(runbooks_dir, "RB-002.md"), "w") as f:
        f.write(rb2)

    print("Successfully created demo data and runbooks in data/")

if __name__ == "__main__":
    create_demo_data()
