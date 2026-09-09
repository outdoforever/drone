"""
Detection Tracker & Spatial Proximity Resolver.
Calculates geographic distances between detections (Haversine formula) to assign nearby hazard flags.
"""

import math
from typing import List, Dict, Any


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes distance between two geographic coordinates in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


class DetectionTracker:
    def __init__(self, proximity_threshold_m: float = 100.0):
        self.proximity_threshold_m = proximity_threshold_m
        self.survivor_counter = 1
        self.fire_counter = 1
        self.flood_counter = 1
        self.debris_counter = 1
        self.structure_counter = 1
        self.smoke_counter = 1

    def generate_id(self, det_type: str) -> str:
        det_type = det_type.lower()
        if det_type == "person":
            id_str = f"SURVIVOR_{self.survivor_counter:03d}"
            self.survivor_counter += 1
        elif det_type == "fire":
            id_str = f"FIRE_{self.fire_counter:03d}"
            self.fire_counter += 1
        elif det_type == "flood":
            id_str = f"FLOOD_{self.flood_counter:03d}"
            self.flood_counter += 1
        elif det_type == "debris":
            id_str = f"DEBRIS_{self.debris_counter:03d}"
            self.debris_counter += 1
        elif det_type == "damaged_structure":
            id_str = f"STRUCTURE_{self.structure_counter:03d}"
            self.structure_counter += 1
        elif det_type == "smoke":
            id_str = f"SMOKE_{self.smoke_counter:03d}"
            self.smoke_counter += 1
        else:
            id_str = f"DET_{self.survivor_counter:03d}"
            self.survivor_counter += 1
        return id_str

    def update_spatial_relationships(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans all active detections, checks distances between survivors and hazards,
        and attaches nearby_fire, nearby_smoke, nearby_flood flags.
        """
        hazards = [d for d in detections if d.get("type") in ["fire", "smoke", "flood"]]
        
        for det in detections:
            if det.get("type") == "person":
                p_lat = det.get("latitude", 0.0)
                p_lon = det.get("longitude", 0.0)
                
                nearby_fire = False
                nearby_smoke = False
                nearby_flood = False
                
                for hazard in hazards:
                    h_lat = hazard.get("latitude", 0.0)
                    h_lon = hazard.get("longitude", 0.0)
                    dist = haversine_distance_meters(p_lat, p_lon, h_lat, h_lon)
                    
                    if dist <= self.proximity_threshold_m:
                        h_type = hazard.get("type")
                        if h_type == "fire":
                            nearby_fire = True
                        elif h_type == "smoke":
                            nearby_smoke = True
                        elif h_type == "flood":
                            nearby_flood = True
                
                det["nearby_fire"] = det.get("nearby_fire", False) or nearby_fire
                det["nearby_smoke"] = det.get("nearby_smoke", False) or nearby_smoke
                det["nearby_flood"] = det.get("nearby_flood", False) or nearby_flood

        return detections
