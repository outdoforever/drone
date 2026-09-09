"""
Pydantic Models for Disaster Drone API & Command Center Payload schemas.
Includes detection, health classification, disaster zones, and mission state.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DetectionItem(BaseModel):
    id: str
    type: str
    confidence: float
    latitude: float
    longitude: float
    timestamp: str
    priority: str
    sector: str = "B4"
    thermal_confirmed: bool = False
    nearby_fire: bool = False
    nearby_smoke: bool = False
    nearby_flood: bool = False
    risk_score: int = 0
    risk_breakdown: Optional[Dict[str, Any]] = None
    # Health classification fields
    health_status: str = "UNKNOWN"
    posture: str = "unknown"
    mobility: str = "unknown"
    environment: str = "open"
    movement_detected: bool = False
    bbox: Optional[List[float]] = None


class DetectionCreateRequest(BaseModel):
    type: str
    confidence: float = 0.90
    latitude: float
    longitude: float
    sector: Optional[str] = "B4"
    thermal_confirmed: Optional[bool] = False


class MissionStatus(BaseModel):
    drone_active: bool = True
    ai_active: bool = True
    gps_status: str = "SIMULATED"
    network_status: str = "ONLINE"
    mission_status: str = "SEARCHING"
    mission_phase: str = "SURVEY"  # SURVEY or SAR
    latitude: float = 0.0
    longitude: float = 0.0
    altitude_m: float = 45.0
    speed_ms: float = 6.5
    battery_pct: float = 94.0
    sector: str = "B4"
    camera_source: str = "none"
    camera_active: bool = False
    mission_location: Optional[Dict[str, Any]] = None


class DetectionSummaryStats(BaseModel):
    total_detections: int
    survivors_total: int
    survivors_critical: int
    survivors_high: int
    survivors_medium: int
    survivors_low: int
    fire_count: int
    flood_count: int
    debris_count: int
    damaged_structures_count: int
    smoke_count: int
    # Health summary
    health_critical_count: int = 0
    health_injured_count: int = 0
    health_stable_count: int = 0


class DisasterZone(BaseModel):
    zone_id: str
    disaster_type: str = "fire"
    boundary_polygon: List[List[float]]
    area_sq_meters: float = 0.0
    coverage_pct: float = 0.0
    severity: str = "MODERATE"
    centroid: Optional[Dict[str, float]] = None
    timestamp: str = ""


class DisasterZoneCreateRequest(BaseModel):
    disaster_type: str = "fire"
    boundary_polygon: List[List[float]]
    area_sq_meters: float = 0.0
    severity: str = "MODERATE"


class CameraStartRequest(BaseModel):
    source: str = "webcam"  # "webcam", file path, or RTSP URL


class MissionPhaseRequest(BaseModel):
    phase: str = "SURVEY"  # SURVEY or SAR


class MissionLocationRequest(BaseModel):
    name: str
    lat: float
    lon: float


class FlightModeRequest(BaseModel):
    mode: str = "AUTOPILOT"  # "AUTOPILOT" or "MANUAL"


class ManualControlCommand(BaseModel):
    vx: float = 0.0      # +East / -West (m/s)
    vy: float = 0.0      # +North / -South (m/s)
    vz: float = 0.0      # +Up / -Down (m/s)
    speed_scale: float = 1.0


class WaypointItem(BaseModel):
    lat: float
    lon: float
    alt: float = 45.0
    action: Optional[str] = "PASS"


class PredefinedPathRequest(BaseModel):
    waypoints: List[WaypointItem]
    loop: bool = True
    auto_start: bool = True


class LiveGPSRequest(BaseModel):
    lat: float
    lon: float
    altitude_m: Optional[float] = 45.0
    speed_ms: Optional[float] = 0.0
    heading_deg: Optional[float] = None
    accuracy_m: Optional[float] = None


