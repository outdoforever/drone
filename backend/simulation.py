"""
Mission Manager & WebSocket Broadcaster for Command Center Dashboard.

Supports two operational phases:
  - SURVEY: Drone maps fire zone boundaries using area_mapper
  - SAR (Search & Rescue): AI detects survivors and classifies health status

Replaces the old SimulationManager with real camera feed support.
"""

import asyncio
import json
import time
import os
import random
from typing import List, Dict, Any, Set, Optional
from fastapi import WebSocket

from ai.risk_engine import RiskEngine
from ai.tracker import DetectionTracker
from ai.gps_simulator import GPSSimulator
from ai.detector import AIDetector
from ai.health import HealthClassifier
from ai.area_mapper import AreaMapper
from backend.database import (
    save_detection, get_all_detections, clear_detections,
    save_zone, get_all_zones, clear_zones
)


class MissionManager:
    """
    Central orchestrator for drone mission operations.
    Manages camera feeds, AI processing, zone mapping, and WebSocket broadcasting.
    """

    def __init__(self):
        self.risk_engine = RiskEngine()
        self.tracker = DetectionTracker()
        self.gps_sim = GPSSimulator()
        self.ai_detector = AIDetector()
        self.health_classifier = HealthClassifier()
        self.area_mapper = AreaMapper()

        self.active_websockets: Set[WebSocket] = set()
        self.is_running = True
        self.simulation_task = None

        # Mission phase: "SURVEY" or "SAR"
        self.mission_phase = "SURVEY"

        # Camera stream state
        self.camera_stream = None
        self.camera_source = "none"
        self.camera_active = False
        self.latest_frame = None
        self.latest_frame_bytes = None
        self._camera_thread = None
        self._stop_camera_worker = False

        # Mission location: None until user sets a zone
        self.mission_location: Optional[Dict] = None

        # DO NOT load seed data — field notes start empty until zone is set
        clear_detections()
        clear_zones()
        print("[MissionManager] Initialized. Awaiting mission zone assignment.")

    def _load_seed_data(self):
        """Legacy seed loader — kept for reference but not called on init."""
        seed_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_detections.json")
        if os.path.exists(seed_path):
            try:
                with open(seed_path, "r") as f:
                    seed_items = json.load(f)
                clear_detections()
                clear_zones()
                for item in seed_items:
                    if item.get("type") == "person":
                        health_result = self.health_classifier.classify(item)
                        item.update(health_result)
                    risk_res = self.risk_engine.calculate_risk(item)
                    item["risk_score"] = risk_res["score"]
                    item["priority"] = risk_res["priority"]
                    item["risk_breakdown"] = risk_res["breakdown"]
                    save_detection(item)
                print(f"[MissionManager] Loaded {len(seed_items)} seed detections.")
            except Exception as e:
                print(f"[MissionManager] Error loading seed data: {e}")

    def set_mission_location(self, name: str, lat: float, lon: float):
        """Set/change the active mission zone. Clears all previous detections and recenters drone."""
        self.mission_location = {"name": name, "lat": lat, "lon": lon}
        self.gps_sim.set_base_location(lat, lon)
        clear_detections()
        clear_zones()
        self.is_running = True
        print(f"[MissionManager] Mission zone set: {name} ({lat}, {lon}). All data cleared.")

    # ──────────────── Flight & Mode Controls ────────────────

    def set_flight_mode(self, mode: str):
        """Toggle flight mode: 'MANUAL' or 'AUTOPILOT'."""
        self.gps_sim.set_flight_mode(mode)

    def manual_command(self, vx: float, vy: float, vz: float = 0.0, speed_scale: float = 1.0):
        """Send manual movement vectors to eVTOL."""
        self.gps_sim.apply_manual_command(vx, vy, vz, speed_scale)

    def set_waypoints(self, waypoints: List[Dict[str, float]], loop: bool = True, auto_start: bool = True):
        """Set predefined waypoint path for autopilot execution."""
        self.gps_sim.set_predefined_path(waypoints, loop=loop, auto_start=auto_start)

    def clear_flight_trail(self):
        """Clear the traversed flight outline."""
        self.gps_sim.clear_traversed_path()

    def clear_waypoints(self):
        """Clear planned path."""
        self.gps_sim.clear_planned_path()

    def update_live_gps(self, lat: float, lon: float, altitude_m: Optional[float] = None, speed_ms: Optional[float] = None, heading_deg: Optional[float] = None):
        """Ingest live GPS location from moving mobile camera/phone and outline the path."""
        self.gps_sim.update_live_gps(lat, lon, altitude_m=altitude_m, speed_ms=speed_ms, heading_deg=heading_deg)
        self.is_running = True

    # ──────────────── Camera Feed Management ────────────────

    def _ipwebcam_gps_loop(self, base_url: str):
        """Polls IP Webcam sensors endpoint for real-time mobile GPS coordinates and compass orientation."""
        import urllib.request
        import json as pyjson
        import math
        print(f"[MissionManager] IP Webcam sensor poller started for {base_url}")
        while self.camera_active and not self._stop_camera_worker:
            try:
                req = urllib.request.Request(f"{base_url}/sensors.json", headers={'User-Agent': 'RescueVisionAI/1.0'})
                with urllib.request.urlopen(req, timeout=1.2) as resp:
                    data = pyjson.loads(resp.read().decode())
                    
                    # 1. Extract Compass / Orientation
                    heading_deg = None
                    if "compass" in data and "data" in data["compass"]:
                        c_data = data["compass"]["data"]
                        if c_data and len(c_data) > 0 and len(c_data[-1]) >= 2:
                            heading_deg = float(c_data[-1][1][0])
                    elif "orientation" in data and "data" in data["orientation"]:
                        o_data = data["orientation"]["data"]
                        if o_data and len(o_data) > 0 and len(o_data[-1]) >= 2:
                            heading_deg = float(o_data[-1][1][0])
                    elif "mag" in data and "data" in data["mag"]:
                        m_data = data["mag"]["data"]
                        if m_data and len(m_data) > 0 and len(m_data[-1]) >= 2:
                            mx, my = float(m_data[-1][1][0]), float(m_data[-1][1][1])
                            heading_deg = (math.degrees(math.atan2(my, mx)) + 360) % 360

                    # 2. Extract GPS Coordinates
                    lat, lon, alt, speed = None, None, 45.0, 0.0
                    if "gps" in data and "data" in data["gps"]:
                        gps_data = data["gps"]["data"]
                        if gps_data and len(gps_data) > 0:
                            latest_gps = gps_data[-1]
                            if len(latest_gps) >= 2 and isinstance(latest_gps[1], list):
                                vals = latest_gps[1]
                                lat, lon = float(vals[0]), float(vals[1])
                                alt = float(vals[2]) if len(vals) > 2 else 45.0
                                speed = float(vals[3]) if len(vals) > 3 else 0.0

                    if lat is not None and lon is not None and (lat != 0.0 or lon != 0.0):
                        self.update_live_gps(lat, lon, altitude_m=alt, speed_ms=speed, heading_deg=heading_deg)
                    elif heading_deg is not None:
                        # Update heading directly if GPS not enabled
                        self.gps_sim.heading_deg = round(heading_deg % 360, 1)
                        self.gps_sim.is_live_tracking = True
                        self.gps_sim.last_live_timestamp = time.time()
                        self.gps_sim.gps_status = "LIVE_MOBILE_GPS"
                        self.gps_sim.status = "MOBILE_CAM_ACTIVE"
            except Exception:
                pass
            time.sleep(0.25)
        print("[MissionManager] IP Webcam sensor poller stopped.")

    def _camera_reader_loop(self):
        """Continuously reads frames from camera stream with high-speed zero-lag frame delivery."""
        import cv2
        import numpy as np
        print("[MissionManager] Camera reader thread active.")
        prev_gray_small = None
        frame_idx = 0

        while self.camera_active and not self._stop_camera_worker and self.camera_stream:
            try:
                result = self.camera_stream.read_frame()
                if result is None:
                    time.sleep(0.005)
                    continue
                frame, metadata = result
                self.latest_frame = frame
                frame_idx += 1

                # If source is already compressed MJPEG, bypass re-encoding for 0ms latency and 0% CPU overhead
                raw_jpg = metadata.get("raw_jpg") if isinstance(metadata, dict) else None
                if raw_jpg:
                    self.latest_frame_bytes = raw_jpg
                else:
                    ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                    if ret:
                        self.latest_frame_bytes = buffer.tobytes()

                # Visual Pan/Rotation Estimation (throttled to every 6th frame on a tiny thumbnail)
                if frame_idx % 6 == 0 and not self.gps_sim.is_live_tracking:
                    try:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        small_gray = cv2.resize(gray, (80, 60))
                        if prev_gray_small is not None:
                            flow = cv2.calcOpticalFlowFarneback(
                                prev_gray_small, small_gray, None,
                                pyr_scale=0.5, levels=1, winsize=9,
                                iterations=1, poly_n=5, poly_sigma=1.1, flags=0
                            )
                            dx = float(np.median(flow[..., 0]))
                            if abs(dx) > 0.4:
                                deg_delta = -(dx / 80.0) * 60.0
                                new_heading = (self.gps_sim.heading_deg + deg_delta) % 360
                                self.gps_sim.heading_deg = round(new_heading, 1)
                        prev_gray_small = small_gray
                    except Exception:
                        pass
                
                time.sleep(0.001)
            except Exception as e:
                print(f"[MissionManager] Camera worker read error: {e}")
                time.sleep(0.01)
        print("[MissionManager] Camera reader thread stopped.")



    def start_camera(self, source: str) -> bool:
        """Start processing a camera feed source."""
        import threading
        from urllib.parse import urlparse
        try:
            from ai.stream import CameraStream
            if self.camera_active or self.camera_stream:
                self.stop_camera()

            self.camera_stream = CameraStream(source=source, loop_video=True)
            if self.camera_stream.open():
                self.camera_source = source
                self.camera_active = True
                self._stop_camera_worker = False
                self._camera_thread = threading.Thread(target=self._camera_reader_loop, daemon=True)
                self._camera_thread.start()

                # If IP Webcam HTTP stream, launch GPS sensor poller
                if source.startswith("http://") or source.startswith("https://"):
                    parsed = urlparse(source)
                    base_url = f"{parsed.scheme}://{parsed.netloc}"
                    self._gps_thread = threading.Thread(target=self._ipwebcam_gps_loop, args=(base_url,), daemon=True)
                    self._gps_thread.start()

                print(f"[MissionManager] Camera started successfully: {source}")
                return True
            else:
                self.camera_active = False
                return False
        except Exception as e:
            print(f"[MissionManager] Camera start error: {e}")
            self.camera_active = False
            return False


    def stop_camera(self):
        """Stop the active camera feed."""
        self._stop_camera_worker = True
        self.camera_active = False
        if self.camera_stream:
            try:
                self.camera_stream.close()
            except Exception:
                pass
        self.camera_stream = None
        self.camera_source = "none"
        self.latest_frame_bytes = None
        self.latest_frame = None
        print("[MissionManager] Camera stopped.")

    def _process_camera_frame(self):
        """
        Process the latest captured frame according to current mission phase.
        Returns any new data generated (zones or detections).
        """
        if not self.camera_active or self.latest_frame is None:
            return None

        frame = self.latest_frame.copy()

        if self.mission_phase == "SURVEY":
            # Area mapping — detect fire zone boundaries
            zones = self.area_mapper.detect_fire_zones(
                frame,
                drone_lat=self.gps_sim.current_lat,
                drone_lon=self.gps_sim.current_lon,
                drone_alt_m=self.gps_sim.altitude_m
            )
            for zone in zones:
                save_zone(zone)
            return {"type": "ZONE_UPDATE", "zones": zones} if zones else None

        elif self.mission_phase == "SAR":
            # Search & Rescue — detect survivors and hazards
            raw_dets = self.ai_detector.process_frame(frame)
            new_items = []
            for det in raw_dets:
                # Assign GPS coords near drone position with slight offset
                det["latitude"] = self.gps_sim.current_lat + random.uniform(-0.0008, 0.0008)
                det["longitude"] = self.gps_sim.current_lon + random.uniform(-0.0008, 0.0008)
                new_item = self.inject_detection(det)
                new_items.append(new_item)
            return {"type": "NEW_DETECTIONS", "detections": new_items} if new_items else None

        return None

    # ──────────────── WebSocket Management ────────────────

    async def connect_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)
        snapshot = self.get_full_state()
        await websocket.send_text(json.dumps({"type": "FULL_STATE", "data": snapshot}))

    def disconnect_websocket(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = set()
        payload = json.dumps(message)
        # Iterate over a copy to avoid RuntimeError if websockets disconnect
        for ws in list(self.active_websockets):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.active_websockets.discard(ws)

    # ──────────────── State Retrieval ────────────────

    def get_full_state(self) -> Dict[str, Any]:
        telemetry = self.gps_sim.get_telemetry()
        telemetry["mission_phase"] = self.mission_phase
        telemetry["camera_source"] = self.camera_source
        telemetry["camera_active"] = self.camera_active
        telemetry["mission_location"] = self.mission_location

        detections = get_all_detections()
        zones = get_all_zones()

        # Summary counts
        survivors = [d for d in detections if d.get("type") == "person"]
        survivors_critical = len([s for s in survivors if s.get("priority") == "CRITICAL"])
        survivors_high = len([s for s in survivors if s.get("priority") == "HIGH"])
        survivors_medium = len([s for s in survivors if s.get("priority") == "MEDIUM"])
        survivors_low = len([s for s in survivors if s.get("priority") == "LOW"])

        # Health counts
        health_critical = len([s for s in survivors if s.get("health_status") == "CRITICAL"])
        health_injured = len([s for s in survivors if s.get("health_status") == "INJURED"])
        health_stable = len([s for s in survivors if s.get("health_status") == "STABLE"])

        stats = {
            "total_detections": len(detections),
            "survivors_total": len(survivors),
            "survivors_critical": survivors_critical,
            "survivors_high": survivors_high,
            "survivors_medium": survivors_medium,
            "survivors_low": survivors_low,
            "fire_count": len([d for d in detections if d.get("type") == "fire"]),
            "flood_count": len([d for d in detections if d.get("type") == "flood"]),
            "debris_count": len([d for d in detections if d.get("type") == "debris"]),
            "damaged_structures_count": len([d for d in detections if d.get("type") == "damaged_structure"]),
            "smoke_count": len([d for d in detections if d.get("type") == "smoke"]),
            "health_critical_count": health_critical,
            "health_injured_count": health_injured,
            "health_stable_count": health_stable,
            "zones_mapped": len(zones)
        }

        alerts = [d for d in detections if d.get("priority") in ["CRITICAL", "HIGH"]]
        alerts.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

        return {
            "telemetry": telemetry,
            "detections": detections,
            "zones": zones,
            "stats": stats,
            "alerts": alerts
        }

    # ──────────────── Detection Injection ────────────────

    def inject_detection(self, det_data: Dict[str, Any]) -> Dict[str, Any]:
        det_type = det_data.get("type", "person").lower()
        new_id = self.tracker.generate_id(det_type)

        item = {
            "id": new_id,
            "type": det_type,
            "confidence": float(det_data.get("confidence", 0.92)),
            "latitude": float(det_data.get("latitude", self.gps_sim.current_lat)),
            "longitude": float(det_data.get("longitude", self.gps_sim.current_lon)),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sector": det_data.get("sector", self.gps_sim.sector),
            "thermal_confirmed": bool(det_data.get("thermal_confirmed", True if det_type == "person" else False)),
            "nearby_fire": bool(det_data.get("nearby_fire", False)),
            "nearby_smoke": bool(det_data.get("nearby_smoke", False)),
            "nearby_flood": bool(det_data.get("nearby_flood", False)),
            "bbox": det_data.get("bbox")
        }

        # Spatial proximity update
        all_dets = get_all_detections()
        all_dets.append(item)
        updated = self.tracker.update_spatial_relationships(all_dets)
        target = [d for d in updated if d["id"] == new_id][0]

        # Health classification for persons
        if det_type == "person":
            health_result = self.health_classifier.classify(target, bbox=det_data.get("bbox"))
            target.update(health_result)

        # Risk calculation
        risk_res = self.risk_engine.calculate_risk(target)
        target["risk_score"] = risk_res["score"]
        target["priority"] = risk_res["priority"]
        target["risk_breakdown"] = risk_res["breakdown"]

        save_detection(target)
        return target

    # ──────────────── Main Loop ────────────────

    async def start_loop(self):
        print("[MissionManager] Starting real-time mission loop.")
        tick = 0
        while True:
            await asyncio.sleep(0.15)
            tick += 1
            if self.is_running:
                telemetry = self.gps_sim.step()

                # Process camera frames with AI if active (every ~0.3s)
                if self.camera_active and tick % 2 == 0:
                    frame_result = self._process_camera_frame()
                    if frame_result:
                        await self.broadcast(frame_result)

                # Simulation fallback: only when no camera AND mission zone is active
                elif not self.camera_active and self.mission_location and tick % 15 == 0:
                    raw_dets = self.ai_detector.simulate_frame_detections()
                    if raw_dets:
                        sample_det = raw_dets[0]
                        lat = self.gps_sim.current_lat + random.uniform(-0.001, 0.001)
                        lon = self.gps_sim.current_lon + random.uniform(-0.001, 0.001)
                        sample_det["latitude"] = lat
                        sample_det["longitude"] = lon
                        new_item = self.inject_detection(sample_det)
                        await self.broadcast({"type": "NEW_DETECTION", "data": new_item})

            # Broadcast live state on every tick
            state = self.get_full_state()
            await self.broadcast({"type": "TELEMETRY_UPDATE", "data": state})



# Global singleton
sim_manager = MissionManager()
