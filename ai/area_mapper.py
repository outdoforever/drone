"""
Fire Zone Boundary Detector & Area Mapper for Autonomous Disaster-Response Drone.

Analyzes drone camera frames to detect fire/burn-affected zones and converts
them into GPS-tagged polygon boundaries for map overlay visualization.

Approach:
    1. Color-space segmentation (HSV) to isolate fire/burn regions in each frame.
    2. Contour extraction to find the boundary of affected areas.
    3. Pixel-to-GPS coordinate conversion using drone altitude + camera FOV.
    4. Polygon simplification for efficient map rendering.
"""

import cv2
import numpy as np
import math
import time
from typing import List, Dict, Any, Optional, Tuple


class AreaMapper:
    """
    Detects fire-affected zone boundaries from drone camera frames
    and produces GPS-tagged polygon coordinates for map overlays.
    """

    # Fire/burn HSV detection ranges
    # Range 1: Active fire (bright orange/yellow flames)
    FIRE_LOW_1 = np.array([0, 100, 150])
    FIRE_HIGH_1 = np.array([25, 255, 255])
    # Range 2: Active fire (red hues)
    FIRE_LOW_2 = np.array([160, 100, 150])
    FIRE_HIGH_2 = np.array([180, 255, 255])
    # Range 3: Burn scars / charred ground (dark, low saturation)
    BURN_LOW = np.array([0, 0, 20])
    BURN_HIGH = np.array([180, 80, 80])

    def __init__(
        self,
        min_contour_area: int = 2000,
        camera_fov_deg: float = 84.0,
        polygon_epsilon_factor: float = 0.015
    ):
        """
        Args:
            min_contour_area: Minimum pixel area for a contour to be considered a valid zone.
            camera_fov_deg: Horizontal field of view of the drone camera in degrees.
            polygon_epsilon_factor: Controls polygon simplification (lower = more detail).
        """
        self.min_contour_area = min_contour_area
        self.camera_fov_deg = camera_fov_deg
        self.polygon_epsilon_factor = polygon_epsilon_factor
        self.zone_counter = 0

    def detect_fire_zones(
        self,
        frame: np.ndarray,
        drone_lat: float,
        drone_lon: float,
        drone_alt_m: float = 50.0,
        drone_heading_deg: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single frame and return detected fire zone polygons.

        Args:
            frame: BGR image from drone camera.
            drone_lat: Current drone latitude.
            drone_lon: Current drone longitude.
            drone_alt_m: Drone altitude in meters.
            drone_heading_deg: Drone heading in degrees (0 = North).

        Returns:
            List of zone dictionaries with GPS polygon boundaries.
        """
        if frame is None:
            return []

        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create combined fire mask
        mask_fire1 = cv2.inRange(hsv, self.FIRE_LOW_1, self.FIRE_HIGH_1)
        mask_fire2 = cv2.inRange(hsv, self.FIRE_LOW_2, self.FIRE_HIGH_2)
        mask_burn = cv2.inRange(hsv, self.BURN_LOW, self.BURN_HIGH)

        # Combine fire masks (active fire + burn scars)
        combined_mask = cv2.bitwise_or(mask_fire1, mask_fire2)
        combined_mask = cv2.bitwise_or(combined_mask, mask_burn)

        # Morphological operations to clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=2)

        # Apply Gaussian blur to smooth boundaries
        combined_mask = cv2.GaussianBlur(combined_mask, (7, 7), 0)
        _, combined_mask = cv2.threshold(combined_mask, 127, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        zones = []
        for contour in contours:
            area_px = cv2.contourArea(contour)
            if area_px < self.min_contour_area:
                continue

            # Simplify polygon
            epsilon = self.polygon_epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) < 3:
                continue

            # Convert pixel coordinates to GPS coordinates
            gps_polygon = []
            for point in approx:
                px, py = point[0]
                lat, lon = self._pixel_to_gps(
                    px, py, w, h,
                    drone_lat, drone_lon, drone_alt_m, drone_heading_deg
                )
                gps_polygon.append([round(lat, 6), round(lon, 6)])

            # Close the polygon
            if gps_polygon[0] != gps_polygon[-1]:
                gps_polygon.append(gps_polygon[0])

            # Calculate approximate area in square meters
            area_sq_m = self._estimate_area_sq_meters(area_px, w, h, drone_alt_m)

            # Calculate fire coverage percentage of frame
            coverage_pct = round((area_px / (w * h)) * 100, 1)

            # Determine severity based on coverage
            if coverage_pct > 40:
                severity = "EXTREME"
            elif coverage_pct > 20:
                severity = "HIGH"
            elif coverage_pct > 8:
                severity = "MODERATE"
            else:
                severity = "LOW"

            self.zone_counter += 1
            zone = {
                "zone_id": f"FIREZONE_{self.zone_counter:03d}",
                "disaster_type": "fire",
                "boundary_polygon": gps_polygon,
                "area_sq_meters": round(area_sq_m, 1),
                "coverage_pct": coverage_pct,
                "severity": severity,
                "centroid": self._compute_centroid(gps_polygon[:-1]),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            zones.append(zone)

        return zones

    def get_fire_mask(self, frame: np.ndarray) -> np.ndarray:
        """
        Returns the binary fire detection mask for visualization/debugging.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, self.FIRE_LOW_1, self.FIRE_HIGH_1)
        mask2 = cv2.inRange(hsv, self.FIRE_LOW_2, self.FIRE_HIGH_2)
        mask3 = cv2.inRange(hsv, self.BURN_LOW, self.BURN_HIGH)
        combined = cv2.bitwise_or(mask1, mask2)
        combined = cv2.bitwise_or(combined, mask3)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=3)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=2)
        return combined

    def _pixel_to_gps(
        self,
        px: float, py: float,
        img_w: int, img_h: int,
        drone_lat: float, drone_lon: float,
        drone_alt_m: float, heading_deg: float
    ) -> Tuple[float, float]:
        """
        Converts pixel (px, py) in the image to (latitude, longitude)
        using pinhole camera model + drone altitude.
        """
        # Ground footprint width/height based on altitude and FOV
        fov_rad = math.radians(self.camera_fov_deg)
        ground_width_m = 2.0 * drone_alt_m * math.tan(fov_rad / 2.0)
        aspect_ratio = img_h / img_w
        ground_height_m = ground_width_m * aspect_ratio

        # Offset from image center in meters
        offset_x_m = ((px / img_w) - 0.5) * ground_width_m
        offset_y_m = (0.5 - (py / img_h)) * ground_height_m  # Y inverted

        # Rotate by drone heading
        heading_rad = math.radians(heading_deg)
        rotated_x = offset_x_m * math.cos(heading_rad) - offset_y_m * math.sin(heading_rad)
        rotated_y = offset_x_m * math.sin(heading_rad) + offset_y_m * math.cos(heading_rad)

        # Convert meters offset to lat/lon offset
        # 1 degree latitude ≈ 111,000 meters
        # 1 degree longitude ≈ 111,000 * cos(lat) meters
        lat_offset = rotated_y / 111000.0
        lon_offset = rotated_x / (111000.0 * math.cos(math.radians(drone_lat)))

        return drone_lat + lat_offset, drone_lon + lon_offset

    def _estimate_area_sq_meters(
        self,
        area_px: float,
        img_w: int, img_h: int,
        drone_alt_m: float
    ) -> float:
        """Estimate real-world area in square meters from pixel area."""
        fov_rad = math.radians(self.camera_fov_deg)
        ground_width_m = 2.0 * drone_alt_m * math.tan(fov_rad / 2.0)
        aspect_ratio = img_h / img_w
        ground_height_m = ground_width_m * aspect_ratio

        total_ground_area = ground_width_m * ground_height_m
        total_px_area = img_w * img_h

        return (area_px / total_px_area) * total_ground_area

    def _compute_centroid(self, polygon: List[List[float]]) -> Dict[str, float]:
        """Compute the centroid of a GPS polygon."""
        if not polygon:
            return {"latitude": 0.0, "longitude": 0.0}
        lat_sum = sum(p[0] for p in polygon)
        lon_sum = sum(p[1] for p in polygon)
        n = len(polygon)
        return {
            "latitude": round(lat_sum / n, 6),
            "longitude": round(lon_sum / n, 6)
        }
