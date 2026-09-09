"""
Simple Survivor Health & Posture Classifier for Disaster-Response Drone.

Prototype version using pose estimation heuristics:
- Standing / Sitting / Lying Down / Trapped (posture from bounding box aspect ratio)
- Mobile / Limited / Immobile (from frame-to-frame movement tracking)
- Environmental context: near_fire, in_water, under_debris (from nearby hazard detections)
"""

import time
from typing import Dict, Any, List, Optional


class HealthClassifier:
    """
    Classifies detected survivors' health status based on:
    1. Bounding box shape (aspect ratio → posture estimation)
    2. Movement history (consecutive frames → mobility)
    3. Environmental hazard proximity (from tracker.py)
    """

    def __init__(self):
        # Movement tracking: detection_id -> list of recent positions
        self._position_history: Dict[str, List[Dict[str, float]]] = {}
        self._max_history = 10

    def classify(
        self,
        detection: Dict[str, Any],
        bbox: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Classify a detected survivor's health status.

        Args:
            detection: Detection dict with at least 'id', 'type', 'latitude', 'longitude'.
            bbox: Optional [x1, y1, x2, y2] bounding box from YOLO.

        Returns:
            Health classification dict.
        """
        det_id = detection.get("id", "UNKNOWN")
        det_type = detection.get("type", "")

        # Only classify persons
        if det_type != "person":
            return {
                "health_status": "N/A",
                "posture": "N/A",
                "mobility": "N/A",
                "environment": "N/A",
                "movement_detected": False
            }

        # 1. Posture estimation from bounding box aspect ratio
        posture = self._estimate_posture(bbox)

        # 2. Mobility from movement tracking
        mobility, movement_detected = self._assess_mobility(det_id, detection)

        # 3. Environmental context from hazard proximity flags
        environment = self._assess_environment(detection)

        # 4. Overall health status
        health_status = self._compute_health_status(posture, mobility, environment)

        return {
            "health_status": health_status,
            "posture": posture,
            "mobility": mobility,
            "environment": environment,
            "movement_detected": movement_detected
        }

    def _estimate_posture(self, bbox: Optional[List[float]]) -> str:
        """
        Estimate posture from bounding box dimensions.
        - Tall + narrow → standing
        - Roughly square → sitting
        - Wide + short → lying_down
        - No bbox → unknown
        """
        if not bbox or len(bbox) < 4:
            return "unknown"

        x1, y1, x2, y2 = bbox
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        if width == 0 or height == 0:
            return "unknown"

        aspect_ratio = height / width

        if aspect_ratio > 1.8:
            return "standing"
        elif aspect_ratio > 1.1:
            return "sitting"
        elif aspect_ratio > 0.4:
            return "lying_down"
        else:
            return "lying_down"

    def _assess_mobility(
        self,
        det_id: str,
        detection: Dict[str, Any]
    ) -> tuple:
        """
        Track position history and determine if the person is moving.
        Returns (mobility_status, movement_detected).
        """
        lat = detection.get("latitude", 0.0)
        lon = detection.get("longitude", 0.0)

        # Add to history
        if det_id not in self._position_history:
            self._position_history[det_id] = []

        history = self._position_history[det_id]
        history.append({"lat": lat, "lon": lon, "time": time.time()})

        # Keep only recent positions
        if len(history) > self._max_history:
            history.pop(0)

        # Need at least 3 data points to assess movement
        if len(history) < 3:
            return "unknown", False

        # Calculate total displacement over recent history
        total_displacement = 0.0
        for i in range(1, len(history)):
            d_lat = history[i]["lat"] - history[i - 1]["lat"]
            d_lon = history[i]["lon"] - history[i - 1]["lon"]
            # Rough displacement in meters
            displacement_m = ((d_lat * 111000) ** 2 + (d_lon * 111000) ** 2) ** 0.5
            total_displacement += displacement_m

        avg_displacement = total_displacement / (len(history) - 1)

        if avg_displacement > 2.0:
            return "mobile", True
        elif avg_displacement > 0.3:
            return "limited", True
        else:
            return "immobile", False

    def _assess_environment(self, detection: Dict[str, Any]) -> str:
        """
        Determine the environmental danger context based on nearby hazard flags.
        Priority: near_fire > in_water > under_debris > open
        """
        if detection.get("nearby_fire"):
            return "near_fire"
        if detection.get("nearby_flood"):
            return "in_water"
        if detection.get("nearby_smoke"):
            return "in_smoke"
        return "open"

    def _compute_health_status(
        self,
        posture: str,
        mobility: str,
        environment: str
    ) -> str:
        """
        Compute overall health status based on combined factors.

        CRITICAL: Lying down + immobile + hazardous environment
        INJURED:  Lying down or immobile
        STABLE:   Standing or mobile
        UNKNOWN:  Insufficient data
        """
        score = 0

        # Posture scoring
        if posture == "lying_down":
            score += 3
        elif posture == "sitting":
            score += 1
        elif posture == "standing":
            score += 0
        elif posture == "unknown":
            score += 1

        # Mobility scoring
        if mobility == "immobile":
            score += 3
        elif mobility == "limited":
            score += 1
        elif mobility == "mobile":
            score += 0
        elif mobility == "unknown":
            score += 1

        # Environmental hazard scoring
        if environment in ("near_fire", "in_water"):
            score += 3
        elif environment == "in_smoke":
            score += 2
        elif environment == "open":
            score += 0

        # Map score to health status
        if score >= 7:
            return "CRITICAL"
        elif score >= 4:
            return "INJURED"
        elif score >= 1:
            return "STABLE"
        else:
            return "STABLE"
