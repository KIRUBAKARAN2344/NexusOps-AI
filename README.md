TRACK_ID=PS07

# NEXUSOPS AI
**Network Incident Intelligence Command Center**

## Project Overview
NexusOps AI is an enterprise-grade network incident triage assistant built for PS07. It ingests streams of network alerts and log events, deterministically groups related alerts into incidents, prioritizes them, and retrieves relevant runbooks via local RAG. Finally, it leverages Gemini to generate initial response recommendations based *strictly* on retrieved evidence, escalating to human operators when the issue is ambiguous or unsupported by existing runbooks.

## Problem Solved
When a network link goes down, it generates a cascade of alerts across dependent devices. Manual triage involves sifting through hundreds of overlapping signals to find the root cause. This project automates the correlation, prioritization, and initial troubleshooting research, empowering operators to start from a grounded recommendation rather than raw alerts.

## Architecture
- **Backend**: Python 3.11 with FastAPI.
- **AI/LLM**: Gemini Pro (via `google-genai` SDK) for reasoning and `gemini-embedding-001` for local RAG embeddings.
- **RAG**: Local FAISS CPU index for runbook retrieval.
- **Deterministic Logic**: Alert normalization, grouping, impact calculation, and escalation thresholds.
- **Frontend**: Custom HTML5 Canvas Topology, CSS Design Tokens, Vanilla JS (served directly by FastAPI). No unnecessary external dependencies.

## AI Workflow (Deterministic vs Gemini)
- **Deterministic**: Alert validation, duplicate detection, grouping overlapping signals into unified incidents, priority calculation, and retrieving local runbooks using FAISS.
- **Gemini**: Analyzing the grouped incident context against retrieved runbooks, producing a structured response (JSON), summarizing the incident, citing specific evidence/runbook clauses, and acknowledging uncertainty.

## Data Description
All data is synthetic and located in `data/`:
- `alerts.json`: A stream of network alerts including normal alerts, duplicates, related alerts (cascades), and noise.
- `devices.json`: Network device inventory and topology context.
- `links.json`: Network links connecting devices.
- `runbooks/`: Markdown runbooks describing standard operating procedures for network issues.

## Demo Scenarios
1. **Normal/Covered Incident**: Multiple related link down and latency alerts cascade into one incident. It matches a local runbook and provides a cited recommendation.
2. **Difficult/Unsupported Incident**: Unrecognized sequence of alerts with no matching runbook. The system groups them but escalates to a human, noting the lack of runbook coverage.
3. **Noise Handling**: Isolated alerts that do not correlate are safely sidelined as noise.

## Setup and Run Instructions
1. Ensure you have Python 3.11 installed.
2. Create a `.env` file with your Gemini API key:
   ```env
   GEMINI_API_KEY="YOUR_API_KEY"
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application (starts on http://localhost:8000):
   ```bash
   python app.py
   ```

## Testing
To run the automated test suite and ensure all backend deterministic logic holds up:
```bash
pytest tests/
```

## Validation Key
VALIDATION_KEY_PLACEHOLDER

## Demo Video
https://youtu.be/Hz2WS7vJsvk
