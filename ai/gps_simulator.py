"""
GPS & Telemetry Simulator for Autonomous Disaster-Response eVTOL.
Supports dual flight modes:
- MANUAL: Operator teleoperation via velocity vectors / keyboard nudges.
- AUTOPILOT: Autonomous navigation along predefined waypoints / outline segments.
Maintains live flight breadcrumb trajectory for tactical map outlining.
"""

import math
import time
from typing import Dict, Any, List, Optional


class GPSSimulator:
    def __init__(self, center_lat: float = 0.0, center_lon: float = 0.0):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.current_lat = center_lat
        self.current_lon = center_lon
        self.altitude_m = 45.0
        self.battery_pct = 94.0
        self.speed_m_s = 6.5
        self.heading_deg = 0.0
        self.angle_rad = 0.0
        self.radius_m = 250.0
        self.sector = "B4"
        self.status = "STANDBY"
        self.drone_active = True
        self.ai_active = True
        self.gps_status = "SIMULATED"
        self.network_status = "ONLINE"

        # Flight mode: 'AUTOPILOT' or 'MANUAL'
        self.flight_mode: str = "AUTOPILOT"

        # Manual control velocity vector: vx (East/West m/s), vy (North/South m/s), vz (Climb m/s)
        self.manual_vx: float = 0.0
        self.manual_vy: float = 0.0
        self.manual_vz: float = 0.0
        self.manual_decay: float = 0.92  # Smooth inertia decay for manual nudges

        # Autopilot Waypoints: list of dicts [{"lat": ..., "lon": ..., "alt": ...}]
        self.planned_path: List[Dict[str, float]] = []
        self.current_waypoint_idx: int = 0
        self.loop_path: bool = True

        # Flight breadcrumb trail: list of [lat, lon]
        self.traversed_path: List[List[float]] = []
        self.max_trail_length: int = 2500

        # Live mobile/camera GPS mode
        self.is_live_tracking: bool = False
        self.last_live_timestamp: float = 0.0


    def set_flight_mode(self, mode: str):
        """Toggle between 'MANUAL' and 'AUTOPILOT'."""
        mode_upper = mode.upper()
        if mode_upper in ("MANUAL", "AUTOPILOT"):
            self.flight_mode = mode_upper
            if mode_upper == "MANUAL":
                self.status = "MANUAL_FLIGHT"
                self.manual_vx = 0.0
                self.manual_vy = 0.0
                self.manual_vz = 0.0
            else:
                self.status = "AUTOPILOT_ACTIVE" if self.planned_path else "SURVEY_ORBIT"
            print(f"[GPSSimulator] Mode set to {self.flight_mode}")

    def apply_manual_command(self, vx: float, vy: float, vz: float = 0.0, speed_scale: float = 1.0):
        """
        Apply velocity commands (in m/s) from manual controller / keyboard.
        vx: +East / -West
        vy: +North / -South
        vz: +Up / -Down
        """
        self.flight_mode = "MANUAL"
        self.status = "MANUAL_FLIGHT"
        max_speed = 12.0 * speed_scale
        self.manual_vx = max(-max_speed, min(max_speed, vx))
        self.manual_vy = max(-max_speed, min(max_speed, vy))
        self.manual_vz = max(-3.0, min(3.0, vz))

        # Calculate heading from vector if moving
        mag = math.hypot(self.manual_vx, self.manual_vy)
        if mag > 0.1:
            self.heading_deg = round((math.degrees(math.atan2(self.manual_vx, self.manual_vy)) + 360) % 360, 1)
            self.speed_m_s = round(mag, 2)

    def set_predefined_path(self, waypoints: List[Dict[str, float]], loop: bool = True, auto_start: bool = True):
        """Set a list of waypoints for autopilot navigation."""
        if not waypoints:
            self.planned_path = []
            self.current_waypoint_idx = 0
            return

        self.planned_path = waypoints
        self.current_waypoint_idx = 0
        self.loop_path = loop
        if auto_start:
            self.flight_mode = "AUTOPILOT"
            self.status = "AUTOPILOT_WAYPOINTS"
        print(f"[GPSSimulator] Predefined path set with {len(waypoints)} waypoints. Loop: {loop}")

    def clear_traversed_path(self):
        """Clear recorded flight breadcrumb trail."""
        self.traversed_path = []
        if self.current_lat != 0.0:
            self.traversed_path.append([self.current_lat, self.current_lon])

    def clear_planned_path(self):
        """Clear planned waypoints."""
        self.planned_path = []
        self.current_waypoint_idx = 0
        if self.flight_mode == "AUTOPILOT":
            self.status = "SEARCHING"

    def update_live_gps(self, lat: float, lon: float, altitude_m: Optional[float] = None, speed_ms: Optional[float] = None, heading_deg: Optional[float] = None):
        """
        Ingests real-time GPS telemetry from a moving mobile camera / device.
        Updates coordinates and appends to traversed flight/movement trail on the map.
        """
        self.is_live_tracking = True
        self.last_live_timestamp = time.time()
        self.gps_status = "LIVE_MOBILE_GPS"
        self.status = "MOBILE_CAM_ACTIVE"

        if self.center_lat == 0.0 and self.center_lon == 0.0:
            self.center_lat = lat
            self.center_lon = lon

        prev_lat, prev_lon = self.current_lat, self.current_lon
        self.current_lat = round(lat, 7)
        self.current_lon = round(lon, 7)

        if altitude_m is not None:
            self.altitude_m = round(altitude_m, 1)

        if heading_deg is not None:
            self.heading_deg = round(heading_deg, 1)
        elif prev_lat != 0.0 and (prev_lat != self.current_lat or prev_lon != self.current_lon):
            d_lat = self.current_lat - prev_lat
            d_lon = self.current_lon - prev_lon
            self.heading_deg = round((math.degrees(math.atan2(d_lon, d_lat)) + 360) % 360, 1)

        if speed_ms is not None:
            self.speed_m_s = round(speed_ms, 2)
        elif prev_lat != 0.0:
            d_lat_m = (self.current_lat - prev_lat) * 111000.0
            d_lon_m = (self.current_lon - prev_lon) * 111000.0 * math.cos(math.radians(self.current_lat))
            self.speed_m_s = round(math.hypot(d_lat_m, d_lon_m) / 1.0, 2)

        self._record_trail()
        self._update_sector()

    def return_to_launch(self):
        """Return to base / mission center coordinates."""
        if self.center_lat == 0.0 and self.center_lon == 0.0:
            return
        self.flight_mode = "AUTOPILOT"
        self.status = "RTL_RETURNING"
        self.planned_path = [{"lat": self.center_lat, "lon": self.center_lon, "alt": 45.0}]
        self.current_waypoint_idx = 0

    def step(self) -> Dict[str, Any]:
        """
        Advances eVTOL state based on active flight mode or live GPS.
        """
        # If live GPS was updated within the last 15 seconds, maintain live position
        if self.is_live_tracking and (time.time() - self.last_live_timestamp < 15.0):
            self.battery_pct = max(5.0, round(self.battery_pct - 0.005, 2))
            return self.get_telemetry()
        elif self.is_live_tracking and (time.time() - self.last_live_timestamp >= 15.0):
            # Live signal timed out, revert to simulated
            self.is_live_tracking = False
            self.gps_status = "SIMULATED"

        # If no base location is set yet, remain standby
        if self.center_lat == 0.0 and self.center_lon == 0.0:
            return self.get_telemetry()

        dt = 0.5  # simulation step delta (seconds)

        if self.flight_mode == "MANUAL":
            self._step_manual(dt)
        else:
            self._step_autopilot(dt)

        # Record position in flight trail if moved
        self._record_trail()

        # Slowly decrease battery
        self.battery_pct = max(5.0, round(self.battery_pct - 0.015, 2))

        # Dynamic sector estimation
        self._update_sector()

        return self.get_telemetry()


    def _step_manual(self, dt: float):
        """Handle manual drone teleoperation physics."""
        meters_lat = self.manual_vy * dt
        meters_lon = self.manual_vx * dt

        # 1 deg lat ~ 111,000m; 1 deg lon ~ 111,000 * cos(lat)
        cos_lat = math.cos(math.radians(self.current_lat)) if self.current_lat != 0 else 1.0
        delta_lat = meters_lat / 111000.0
        delta_lon = meters_lon / (111000.0 * max(0.01, cos_lat))

        self.current_lat = round(self.current_lat + delta_lat, 7)
        self.current_lon = round(self.current_lon + delta_lon, 7)
        self.altitude_m = round(max(5.0, min(150.0, self.altitude_m + self.manual_vz * dt)), 1)

        # Apply inertia decay so drone smoothly slows down if input stops
        self.manual_vx *= self.manual_decay
        self.manual_vy *= self.manual_decay
        self.manual_vz *= self.manual_decay

        speed = math.hypot(self.manual_vx, self.manual_vy)
        self.speed_m_s = round(speed, 2)
        if speed < 0.1:
            self.speed_m_s = 0.0
            self.status = "MANUAL_HOLD"
        else:
            self.status = "MANUAL_FLIGHT"

    def _step_autopilot(self, dt: float):
        """Handle autonomous navigation along waypoints or default survey orbit."""
        if self.planned_path and len(self.planned_path) > 0:
            # Navigate to current target waypoint
            target_wp = self.planned_path[self.current_waypoint_idx]
            target_lat = target_wp["lat"]
            target_lon = target_wp["lon"]
            target_alt = target_wp.get("alt", 45.0)

            # Calculate distance and bearing to waypoint
            cos_lat = math.cos(math.radians(self.current_lat))
            d_lat_m = (target_lat - self.current_lat) * 111000.0
            d_lon_m = (target_lon - self.current_lon) * 111000.0 * cos_lat
            dist_m = math.hypot(d_lat_m, d_lon_m)

            # Heading calculation
            self.heading_deg = round((math.degrees(math.atan2(d_lon_m, d_lat_m)) + 360) % 360, 1)

            # Waypoint reached threshold (within ~6 meters)
            if dist_m < 6.0:
                if self.current_waypoint_idx < len(self.planned_path) - 1:
                    self.current_waypoint_idx += 1
                    self.status = f"NAV_TO_WP_{self.current_waypoint_idx + 1}"
                elif self.loop_path:
                    self.current_waypoint_idx = 0
                    self.status = "AUTOPILOT_LOOPING"
                else:
                    self.status = "PATH_COMPLETED"
                    self.speed_m_s = 0.0
                    return
            else:
                self.status = f"WAYPOINT_{self.current_waypoint_idx + 1}_OF_{len(self.planned_path)}"

            # Step towards target waypoint at cruise speed
            cruise_speed = 7.5  # m/s
            self.speed_m_s = cruise_speed
            step_dist = min(dist_m, cruise_speed * dt)
            angle = math.atan2(d_lon_m, d_lat_m)

            move_lat = (step_dist * math.cos(angle)) / 111000.0
            move_lon = (step_dist * math.sin(angle)) / (111000.0 * cos_lat)

            self.current_lat = round(self.current_lat + move_lat, 7)
            self.current_lon = round(self.current_lon + move_lon, 7)

            # Smoothly interpolate altitude
            d_alt = target_alt - self.altitude_m
            if abs(d_alt) > 0.5:
                self.altitude_m += math.copysign(min(abs(d_alt), 1.5 * dt), d_alt)
                self.altitude_m = round(self.altitude_m, 1)

        else:
            # Default: Lawnmower/Orbit survey around center_lat, center_lon
            self.angle_rad += 0.06
            if self.angle_rad > 2 * math.pi:
                self.angle_rad -= 2 * math.pi

            lat_offset = (self.radius_m * math.sin(self.angle_rad)) / 111000.0
            lon_offset = (self.radius_m * math.cos(self.angle_rad)) / (111000.0 * math.cos(math.radians(self.center_lat)))

            prev_lat, prev_lon = self.current_lat, self.current_lon
            self.current_lat = round(self.center_lat + lat_offset, 7)
            self.current_lon = round(self.center_lon + lon_offset, 7)

            # Heading based on orbit velocity
            d_lat = self.current_lat - prev_lat
            d_lon = self.current_lon - prev_lon
            if abs(d_lat) > 1e-7 or abs(d_lon) > 1e-7:
                self.heading_deg = round((math.degrees(math.atan2(d_lon, d_lat)) + 360) % 360, 1)

            self.speed_m_s = 6.5
            self.status = "SURVEY_ORBIT"

    def _record_trail(self):
        """Append to breadcrumbs if position changed."""
        if self.current_lat == 0.0 and self.current_lon == 0.0:
            return
        
        point = [self.current_lat, self.current_lon]
        if not self.traversed_path:
            self.traversed_path.append(point)
            return

        last_pt = self.traversed_path[-1]
        # High precision for live mobile tracking (0.3m threshold)
        d_lat = (point[0] - last_pt[0]) * 111000.0
        d_lon = (point[1] - last_pt[1]) * 111000.0
        if math.hypot(d_lat, d_lon) >= 0.3:
            self.traversed_path.append(point)
            if len(self.traversed_path) > self.max_trail_length:
                self.traversed_path.pop(0)


    def _update_sector(self):
        if self.center_lat == 0.0:
            return
        lat_diff = self.current_lat - self.center_lat
        lon_diff = self.current_lon - self.center_lon
        if lat_diff >= 0 and lon_diff >= 0:
            self.sector = "NE-B4"
        elif lat_diff >= 0 and lon_diff < 0:
            self.sector = "NW-A2"
        elif lat_diff < 0 and lon_diff < 0:
            self.sector = "SW-C1"
        else:
            self.sector = "SE-D3"

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "latitude": self.current_lat,
            "longitude": self.current_lon,
            "altitude_m": self.altitude_m,
            "speed_ms": self.speed_m_s,
            "heading_deg": self.heading_deg,
            "battery_pct": self.battery_pct,
            "sector": self.sector,
            "flight_mode": self.flight_mode,
            "drone_active": self.drone_active,
            "ai_active": self.ai_active,
            "gps_status": self.gps_status,
            "network_status": self.network_status,
            "mission_status": self.status,
            "current_waypoint_idx": self.current_waypoint_idx,
            "total_waypoints": len(self.planned_path),
            "traversed_path": self.traversed_path,
            "planned_path": self.planned_path,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    def set_base_location(self, lat: float, lon: float):
        """Recenters the drone and initializes its starting position."""
        self.center_lat = lat
        self.center_lon = lon
        self.current_lat = lat
        self.current_lon = lon
        self.angle_rad = 0.0
        self.battery_pct = 94.0
        self.status = "HOLD" if self.flight_mode == "MANUAL" else "SURVEY_ORBIT"
        self.traversed_path = [[lat, lon]]
        print(f"[GPSSimulator] Base location initialized to ({lat}, {lon})")

