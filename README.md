# Autonomous Disaster-Response Drone — 20% Software Prototype

This repository implements the **20% Software Prototype** for the Autonomous Disaster-Response Drone system, demonstrating the complete intelligence workflow:

> **Detect → Locate → Assess → Prioritize → Visualize**

---

## 🌟 Key Features

1. **AI Detection Engine**
   - Detects disaster categories: `person`, `fire`, `smoke`, `flood`, `debris`, `damaged_structure`.
   - Incorporates confidence scores and simulated thermal image verification.

2. **MongoDB Database & Environment Configuration**
   - Integrated MongoDB backend using PyMongo & python-dotenv (`.env`).
   - Stores detections, risk calculations, and mission telemetry in MongoDB collections (`detections`, `mission_logs`).

3. **GPS & Telemetry Simulator**
   - Programmatically simulates drone flight trajectories, altitude, battery level, speed, and active disaster sectors (e.g. Coimbatore Sector B4).

3. **Risk Engine & Rescue Prioritization**
   - Evaluates victim priority using a multi-factor scoring matrix:
     - Confirmed Person: `+30`
     - Thermal Confirmation: `+20`
     - Nearby Fire (<100m): `+25`
     - Nearby Smoke (<100m): `+10`
     - High Confidence (≥85%): `+15`
   - Maps scores to Priority Levels: `CRITICAL` (81–100), `HIGH` (61–80), `MEDIUM` (31–60), `LOW` (0–30).

4. **Zero-Camera Command Center Dashboard**
   - Built with React + Vite + Leaflet mapping.
   - Designed explicitly **without camera/video feeds**, displaying processed spatial disaster intelligence and real-time survivor priority alerts.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js v18+

### Installation & Launch

1. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn pymongo motor python-dotenv pydantic pytest
   cd frontend && npm install && cd ..
   ```

2. **Configure Environment Variables (`.env`)**:
   Open `.env` (or `backend/.env`) and paste your MongoDB connection URI:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=disaster_drone
   ```

3. **Run the System**:
   ```bash
   python run_app.py
   ```

3. **Open Command Center**:
   - **Dashboard**: [http://localhost:3000](http://localhost:3000)
   - **FastAPI API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Unit Tests

Run the backend unit test suite:
```bash
python -m pytest tests/
```

---

## 📁 System Architecture

```text
disaster-drone-prototype/
├── ai/
│   ├── detector.py           # AI Detection & Vision pipeline
│   ├── risk_engine.py        # Risk scoring matrix algorithm
│   ├── tracker.py            # Haversine spatial proximity calculator
│   └── gps_simulator.py      # Drone trajectory telemetry simulator
│
├── backend/
│   ├── main.py               # FastAPI server & endpoints
│   ├── database.py           # SQLite database layer
│   ├── models.py             # Pydantic data schemas
│   └── simulation.py         # Live loop & WebSocket broadcaster
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DisasterMap.jsx        # Leaflet map with custom markers
│   │   │   ├── MissionStatus.jsx      # Header & Telemetry indicators
│   │   │   ├── DetectionSummary.jsx   # Survivor & hazard metrics
│   │   │   ├── PriorityAlerts.jsx     # Live urgent alerts feed
│   │   │   ├── AIInsights.jsx         # Detail risk breakdown panel
│   │   │   └── SimulationControls.jsx # Scan controls & demo injectors
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── data/
│   └── sample_detections.json # Seed dataset
│
├── tests/
│   └── test_risk_engine.py    # Pytest unit tests
│
└── run_app.py                 # Single launcher script
```
