# Autonomous Disaster-Response Drone — 20% Software Prototype

## 1. Prototype Objective

This prototype represents approximately **20% of the complete autonomous disaster-response drone system**.

The goal is to demonstrate the core software intelligence pipeline:

> **Detect → Locate → Assess → Prioritize → Visualize**

The prototype focuses on the software layer and does **not** attempt to implement the complete autonomous drone, navigation, thermal hardware integration, or advanced communication stack.

The dashboard is intentionally designed **without a camera/video feed**. It displays processed disaster intelligence rather than raw camera footage.

---

# 2. Core Prototype Concept

```text
              INPUT
                │
                ▼
        Disaster Image/Video
                │
                ▼
          AI Detection
                │
        ┌───────┴────────┐
        ▼                ▼
    Survivors         Hazards
        │                │
        └───────┬────────┘
                ▼
          Simulated GPS
                │
                ▼
        Risk Assessment
                │
                ▼
       Rescue Prioritization
                │
                ▼
        Detection Database
                │
        ┌───────┴────────┐
        ▼                ▼
    Disaster Map      Alert System
        │                │
        └───────┬────────┘
                ▼
        COMMAND DASHBOARD
```

---

# 3. Scope of the 20% Prototype

## Included

### A. AI Detection
The prototype will detect a limited number of disaster-related classes:

- `person`
- `fire`
- `smoke`
- `flood`
- `debris`
- `damaged_structure`

The initial implementation can use a lightweight YOLO-family object-detection model.

---

### B. Detection Information

Every detection should generate structured information such as:

```json
{
  "id": "SURVIVOR_001",
  "type": "person",
  "confidence": 0.94,
  "latitude": 11.0168,
  "longitude": 76.9558,
  "timestamp": "2026-09-08T14:30:21",
  "priority": "CRITICAL"
}
```

Each detection should contain:

- Unique detection ID
- Detection type
- Confidence score
- Latitude
- Longitude
- Timestamp
- Priority/risk level

---

# 4. Simulated Drone/GPS Input

A physical drone is **not required** for this prototype.

The system can initially use:

- Pre-recorded disaster images
- Pre-recorded drone footage
- Laptop webcam
- Simulated drone telemetry
- Simulated GPS coordinates

Example:

```text
Input:
Disaster video

      ↓

AI:
Person detected

      ↓

Simulated GPS:
11.0168, 76.9558

      ↓

Dashboard:
SURVIVOR #001
```

Later, simulated GPS can be replaced by real GPS data from the drone.

---

# 5. Risk Assessment Engine

The system should not only report:

> "Person detected."

It should evaluate the situation and produce a priority level.

## Example factors

```text
Person confidence
Thermal confirmation (simulated for prototype)
Nearby fire
Nearby flood
Nearby smoke
Immobility
Isolation
```

For the first prototype, a simple rule-based score is sufficient.

### Example scoring

```text
Confirmed person          +30
Thermal confirmation      +20
Fire nearby               +25
Smoke nearby              +10
High detection confidence +15
```

Maximum:

```text
100
```

### Priority levels

```text
81–100  → CRITICAL
61–80   → HIGH
31–60   → MEDIUM
0–30    → LOW
```

### Example

```text
SURVIVOR #001

Person confidence: 94%
Thermal confirmation: YES
Fire nearby: YES

Risk Score: 92/100

Priority: CRITICAL
```

---

# 6. Thermal Camera — Prototype Approach

A real thermal camera is **out of scope for the first 20% prototype**.

Instead, the thermal result can initially be simulated.

Example:

```text
RGB Detection:
Person → 87%

Simulated Thermal:
Human heat signature → YES

Result:
SURVIVOR CONFIRMED
```

This keeps the software architecture ready for future RGB + thermal fusion without requiring thermal hardware at this stage.

---

# 7. Disaster Map

The dashboard will contain a map instead of a camera feed.

The map should display:

- Survivor locations
- Fire locations
- Flood locations
- Debris locations
- Damaged structure locations
- Drone position
- Search area (basic/simulated)

Example:

```text
                DISASTER MAP

          🔴 FIRE

                    🟢 SURVIVOR


     🟠 DEBRIS


                         🟢 SURVIVOR


               🔵 FLOOD
```

Clicking a marker should display its details.

Example:

```text
SURVIVOR #001

Confidence: 94%
Priority: CRITICAL
Thermal: Confirmed

Coordinates:
11.0168, 76.9558
```

---

# 8. Command Center Dashboard

## Important

The dashboard will **NOT contain a camera/video panel**.

The dashboard is designed to show **actionable intelligence**, not raw video.

## Proposed layout

```text
┌─────────────────────────────────────────────────────┐
│        DISASTER RESPONSE COMMAND CENTER             │
├────────────────────────────┬────────────────────────┤
│                            │ MISSION STATUS         │
│                            │                        │
│       DISASTER MAP         │ 🟢 DRONE ACTIVE        │
│                            │ 🟢 AI ACTIVE           │
│      🔴 Fire               │ 🟢 GPS ACTIVE          │
│                            │ 🟢 NETWORK ONLINE      │
│      🟢 Survivor           │                        │
│                            ├────────────────────────┤
│      🟠 Debris             │ SURVIVOR SUMMARY      │
│                            │                        │
│      🔵 Flood              │ Critical: 2            │
│                            │ High: 4                │
│                            │ Medium: 3              │
├────────────────────────────┼────────────────────────┤
│ DETECTION SUMMARY          │ PRIORITY ALERTS        │
│                            │                        │
│ Survivors: 9               │ 🔴 Survivor #003       │
│ Fire: 3                    │    Risk: 94/100       │
│ Flood: 2                   │                        │
│ Debris: 7                  │ 🔴 Survivor #007       │
│ Damaged Areas: 5           │    Risk: 87/100       │
└────────────────────────────┴────────────────────────┘
```

---

# 9. Dashboard Components

## 9.1 Disaster Map

Shows geographically tagged detections.

## 9.2 Mission Status

Shows:

```text
Drone: ACTIVE
AI: ACTIVE
GPS: ACTIVE
Network: ONLINE/OFFLINE
Mission: SEARCHING
```

## 9.3 Detection Statistics

Example:

```text
Survivors           9
Fire                3
Flood               2
Debris              7
Damaged Structures  5
```

## 9.4 Priority Alerts

Example:

```text
🔴 CRITICAL
Survivor #003
Risk Score: 94
Sector: B4
```

## 9.5 AI Insights

Example:

```text
SURVIVOR #003

Confidence: 94%
Thermal: Confirmed
Nearby Fire: Yes
Nearby Flood: No

Risk Score: 94/100
Priority: CRITICAL
```

---

# 10. Proposed Software Architecture

```text
                    INPUT DATA
                        │
                        ▼
                ┌──────────────┐
                │  AI DETECTOR │
                │    YOLO      │
                └──────┬───────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        PERSON DETECTION     HAZARD DETECTION
             │                   │
             └─────────┬─────────┘
                       ▼
                ┌──────────────┐
                │ GPS MODULE   │
                │ (SIMULATED)  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │ RISK ENGINE  │
                └──────┬───────┘
                       │
                       ▼
                ┌──────────────┐
                │   DATABASE   │
                └──────┬───────┘
                       │
                ┌──────┴───────┐
                ▼              ▼
          MAP SERVICE      ALERT SERVICE
                │              │
                └──────┬───────┘
                       ▼
             COMMAND DASHBOARD
```

---

# 11. Technology Stack

## AI / Computer Vision

- Python
- OpenCV
- YOLO
- PyTorch

## Backend

Recommended:

- Python
- FastAPI
- WebSocket
- SQLite

SQLite is sufficient for the prototype. PostgreSQL can be introduced later.

## Frontend

- React
- JavaScript or TypeScript
- Leaflet or MapLibre

## Data Format

JSON for detection and telemetry data.

Example:

```json
{
  "id": "FIRE_001",
  "type": "fire",
  "confidence": 0.89,
  "latitude": 11.0172,
  "longitude": 76.9563,
  "timestamp": "2026-09-08T14:31:02",
  "priority": "HIGH"
}
```

---

# 12. Suggested Project Structure

```text
disaster-drone-prototype/
│
├── ai/
│   ├── detector.py
│   ├── risk_engine.py
│   ├── tracker.py
│   └── detection_data.json
│
├── backend/
│   ├── main.py
│   ├── database.py
│   └── models.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DisasterMap.jsx
│   │   │   ├── MissionStatus.jsx
│   │   │   ├── DetectionSummary.jsx
│   │   │   ├── PriorityAlerts.jsx
│   │   │   └── AIInsights.jsx
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   └── package.json
│
├── data/
│   ├── images/
│   └── sample_detections.json
│
└── README.md
```

---

# 13. Development Workflow

Build the prototype in this order.

## Step 1 — AI Detection

```text
Image/Video
    ↓
YOLO
    ↓
Person/Hazard
```

Goal:

```text
PERSON 94%
FIRE 89%
DEBRIS 82%
```

---

## Step 2 — Detection Data

Convert each detection into structured JSON.

```text
Detection
+ Confidence
+ Timestamp
+ Location
```

---

## Step 3 — Risk Engine

```text
Detection
    ↓
Risk calculation
    ↓
Priority
```

Example:

```text
Person + Fire nearby
        ↓
Risk Score 92
        ↓
CRITICAL
```

---

## Step 4 — Backend

```text
AI
 ↓
FastAPI
 ↓
Database
```

The backend stores and serves detection information.

---

## Step 5 — Dashboard

```text
FastAPI
   ↓
React
   ↓
Map + Alerts + Statistics
```

---

## Step 6 — Integration

Final prototype flow:

```text
Disaster Image/Video
        ↓
      YOLO
        ↓
  Detection Result
        ↓
 Simulated GPS
        ↓
   Risk Engine
        ↓
     Database
        ↓
      API
        ↓
    Dashboard
        ↓
Map + Priority + Alerts
```

---

# 14. Prototype Demonstration

The final demo should be simple and repeatable.

## Demo Sequence

### 1. Start Command Center

```text
DRONE: ACTIVE
AI: ACTIVE
GPS: SIMULATED
NETWORK: ONLINE
```

### 2. Start a disaster video or image stream

The AI processes the input.

### 3. Person detected

```text
PERSON
Confidence: 94%
```

### 4. Detection is localized

```text
SURVIVOR #001

Location:
11.0168, 76.9558
```

### 5. Risk Engine evaluates

```text
Thermal confirmation: YES
Fire nearby: YES

Risk Score: 92/100
Priority: CRITICAL
```

### 6. Dashboard updates

A survivor marker appears on the map.

### 7. Alert appears

```text
⚠️ CRITICAL SURVIVOR DETECTED

SURVIVOR #001
Risk: 92/100
Location: Sector B4

Recommended Action:
Immediate rescue response
```

---

# 15. What Is NOT Part of the 20% Prototype

The following should be treated as future development:

- Real drone flight control
- Autonomous waypoint navigation
- GPS-denied navigation
- SLAM
- VIO
- Real obstacle avoidance
- Real thermal camera integration
- Advanced RGB + thermal sensor fusion
- Qualcomm hardware optimization
- 5G communication
- Long-range radio communication
- Multi-drone coordination
- 3D mapping
- Automatic safe-route generation
- Advanced mission planning
- Full disaster-area orthomosaic generation
- Real-time drone video in dashboard

These features can be represented in the **future architecture**, but they do not need to be implemented in the 20% prototype.

---

# 16. Future Expansion

The prototype should be designed so that the missing components can be added later.

```text
                 CURRENT 20%
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      YOLO       Risk Engine      Map
        │            │            │
        └────────────┼────────────┘
                     ▼
                Dashboard


                 FUTURE 80%
                     │
     ┌───────────────┼────────────────┐
     ▼               ▼                ▼
  Thermal          SLAM          Autonomous Flight
     │               │                │
     ▼               ▼                ▼
Sensor Fusion   GPS-denied       Mission Planning
                     │
     ┌───────────────┼────────────────┐
     ▼               ▼                ▼
    5G            Multi-drone      3D Mapping
```

---

# 17. Final 20% Deliverable

At the end of the prototype, the team should be able to demonstrate:

```text
✅ AI detects survivors and selected hazards
✅ Detection has confidence score
✅ Detection receives a location
✅ Risk score is calculated
✅ Survivor receives rescue priority
✅ Detection is stored
✅ Detection appears on a live map
✅ Command dashboard displays mission intelligence
✅ Dashboard works without a camera panel
```

The central result is:

> **The system converts disaster imagery into structured, location-aware and priority-ranked information for emergency responders.**

---

# 18. One-Line Project Pitch

> **An edge-AI disaster intelligence system that detects survivors and hazards, localizes them, calculates rescue priority, and visualizes actionable information on a command-center map.**
