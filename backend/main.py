"""
FastAPI Server for Autonomous Disaster-Response Drone Command Center.
Supports SURVEY (area mapping) and SAR (search & rescue) mission phases.
"""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List

from backend.database import init_db, get_all_detections, clear_detections, get_all_zones, clear_zones
from backend.simulation import sim_manager
from backend.models import (
    DetectionCreateRequest, MissionStatus, CameraStartRequest,
    MissionPhaseRequest, DisasterZoneCreateRequest, MissionLocationRequest,
    FlightModeRequest, ManualControlCommand, PredefinedPathRequest, LiveGPSRequest
)



app = FastAPI(
    title="Autonomous Disaster-Response Drone API",
    description="Detect → Locate → Assess → Prioritize → Visualize | SURVEY + SAR Phases",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()
    sim_manager.simulation_task = asyncio.create_task(sim_manager.start_loop())


# ──────────────── Status & Data Endpoints ────────────────

@app.get("/")
def read_root():
    return {
        "system": "Autonomous Disaster-Response Drone — Command Center",
        "status": "ONLINE",
        "pipeline": "Detect → Locate → Assess → Prioritize → Visualize",
        "mission_phase": sim_manager.mission_phase,
        "camera_active": sim_manager.camera_active
    }


@app.get("/api/status")
def get_mission_status():
    telemetry = sim_manager.gps_sim.get_telemetry()
    telemetry["mission_phase"] = sim_manager.mission_phase
    telemetry["camera_source"] = sim_manager.camera_source
    telemetry["camera_active"] = sim_manager.camera_active
    return telemetry


@app.get("/api/detections")
def get_detections():
    return get_all_detections()


@app.get("/api/zones")
def get_zones():
    return get_all_zones()


@app.get("/api/alerts")
def get_priority_alerts():
    detections = get_all_detections()
    alerts = [d for d in detections if d.get("priority") in ["CRITICAL", "HIGH"]]
    alerts.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return alerts


# ──────────────── Mission Phase Control ────────────────

@app.post("/api/mission/phase")
def set_mission_phase(req: MissionPhaseRequest):
    phase = req.phase.upper()
    if phase not in ("SURVEY", "SAR"):
        raise HTTPException(status_code=400, detail="Phase must be 'SURVEY' or 'SAR'")
    sim_manager.mission_phase = phase
    sim_manager.gps_sim.status = f"{phase}_ACTIVE"
    return {"message": f"Mission phase set to {phase}", "phase": phase}


# ──────────────── Camera Feed Control ────────────────

@app.post("/api/stream/start")
async def start_camera_stream(req: CameraStartRequest):
    success = sim_manager.start_camera(req.source)
    if success:
        state = sim_manager.get_full_state()
        await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
        return {"message": f"Camera started: {req.source}", "active": True}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to open camera source: {req.source}")


@app.post("/api/stream/stop")
async def stop_camera_stream():
    sim_manager.stop_camera()
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Camera stopped", "active": False}


async def generate_mjpeg_stream():
    last_frame_ref = None
    while True:
        curr_frame = sim_manager.latest_frame_bytes
        if curr_frame is not None and curr_frame is not last_frame_ref:
            last_frame_ref = curr_frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + curr_frame + b'\r\n')
        await asyncio.sleep(0.005)


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive"
        }
    )


@app.post("/api/mission/location")
async def set_mission_location(req: MissionLocationRequest):
    sim_manager.set_mission_location(req.name, req.lat, req.lon)
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "FULL_STATE", "data": state})
    return {"message": f"Mission zone set to {req.name}", "location": req.dict()}


# ──────────────── Drone Flight Mode & Navigation ────────────────

@app.post("/api/drone/mode")
async def set_drone_flight_mode(req: FlightModeRequest):
    sim_manager.set_flight_mode(req.mode)
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": f"Flight mode switched to {req.mode}", "flight_mode": req.mode}


@app.post("/api/drone/manual")
async def manual_drone_control(req: ManualControlCommand):
    sim_manager.manual_command(req.vx, req.vy, req.vz, req.speed_scale)
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Manual command applied", "vx": req.vx, "vy": req.vy, "vz": req.vz}


@app.post("/api/drone/waypoints")
async def set_drone_waypoints(req: PredefinedPathRequest):
    wp_list = [w.dict() for w in req.waypoints]
    sim_manager.set_waypoints(wp_list, loop=req.loop, auto_start=req.auto_start)
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "FULL_STATE", "data": state})
    return {"message": f"Assigned {len(wp_list)} waypoints", "waypoints_count": len(wp_list)}


@app.post("/api/drone/clear_trail")
async def clear_drone_trail():
    sim_manager.clear_flight_trail()
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Flight trail cleared"}


@app.post("/api/drone/clear_waypoints")
async def clear_drone_waypoints():
    sim_manager.clear_waypoints()
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "FULL_STATE", "data": state})
    return {"message": "Waypoints cleared"}


@app.post("/api/drone/rtl")
async def return_to_launch():
    sim_manager.return_to_launch()
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Return To Launch initiated"}


@app.post("/api/drone/mobile_gps")
async def receive_mobile_gps(req: LiveGPSRequest):
    """Receives live GPS telemetry from mobile device camera and draws the moving path."""
    sim_manager.update_live_gps(
        lat=req.lat,
        lon=req.lon,
        altitude_m=req.altitude_m,
        speed_ms=req.speed_ms,
        heading_deg=req.heading_deg
    )
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Mobile GPS coordinates updated", "lat": req.lat, "lon": req.lon}



# ──────────────── Simulation Lifecycle & Injection ────────────────

@app.post("/api/simulation/start")
@app.post("/api/mission/start")
async def start_simulation():
    sim_manager.is_running = True
    sim_manager.gps_sim.status = "SEARCHING"
    sim_manager.gps_sim.drone_active = True
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Simulation started", "status": "SEARCHING"}


@app.post("/api/simulation/pause")
@app.post("/api/mission/pause")
async def pause_simulation():
    sim_manager.is_running = False
    sim_manager.gps_sim.status = "PAUSED"
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "Simulation paused", "status": "PAUSED"}


@app.post("/api/simulation/reset")
@app.post("/api/mission/reset")
async def reset_simulation():
    clear_detections()
    clear_zones()
    sim_manager._load_seed_data()
    state = sim_manager.get_full_state()
    await sim_manager.broadcast({"type": "TELEMETRY_UPDATE", "data": state})
    return {"message": "All detections and zones reset to initial state"}


@app.post("/api/mission/inject_survivor")
async def inject_survivor():
    det = sim_manager.inject_detection({
        "type": "person",
        "confidence": 0.95,
        "thermal_confirmed": True
    })
    await sim_manager.broadcast({"type": "NEW_DETECTION", "data": det})
    return {"message": "Survivor injected", "detection": det}


@app.post("/api/mission/inject_fire")
async def inject_fire():
    det = sim_manager.inject_detection({
        "type": "fire",
        "confidence": 0.92,
        "thermal_confirmed": True,
        "nearby_fire": True
    })
    await sim_manager.broadcast({"type": "NEW_DETECTION", "data": det})
    return {"message": "Fire injected", "detection": det}


@app.post("/api/simulation/inject")
async def inject_detection(req: DetectionCreateRequest):
    new_det = sim_manager.inject_detection(req.dict())
    await sim_manager.broadcast({"type": "NEW_DETECTION", "data": new_det})
    return {"message": "Detection injected successfully", "detection": new_det}


# ──────────────── WebSocket Live Stream ────────────────

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await sim_manager.connect_websocket(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        sim_manager.disconnect_websocket(websocket)
