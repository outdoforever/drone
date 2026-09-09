"""
Risk Assessment Engine for Autonomous Disaster-Response Drone.
Calculates priority scores and levels based on detected targets, environmental hazards,
simulated thermal imaging, health classification, and detection confidence.

Expanded scoring matrix with survivor health factors.
"""

from typing import Dict, Any


class RiskEngine:
    """
    Evaluates risk score (0 to 100) and assigns priority levels.

    Scoring Matrix:
    ─────────────────────────────────────────────
    Factor                          Points
    ─────────────────────────────────────────────
    Confirmed person                +20
    Thermal confirmation            +10
    Fire nearby (<100m)             +15
    Smoke nearby (<100m)            +5
    Flood/water nearby (<100m)      +10
    High confidence (>= 85%)        +5
    Health: CRITICAL                +20
    Health: INJURED                 +10
    Posture: lying_down / trapped   +10
    Mobility: immobile              +10
    Environment: hazardous          +5
    ─────────────────────────────────────────────
    Maximum: 100 (capped)

    Priority Levels:
      81 - 100 → CRITICAL
      61 - 80  → HIGH
      31 - 60  → MEDIUM
      0  - 30  → LOW
    """

    def calculate_risk(self, detection: Dict[str, Any]) -> Dict[str, Any]:
        det_type = detection.get("type", "").lower()
        confidence = float(detection.get("confidence", 0.0))
        thermal_confirmed = bool(detection.get("thermal_confirmed", False))
        nearby_fire = bool(detection.get("nearby_fire", False))
        nearby_smoke = bool(detection.get("nearby_smoke", False))
        nearby_flood = bool(detection.get("nearby_flood", False))

        # Health fields (from health.py classifier)
        health_status = detection.get("health_status", "UNKNOWN")
        posture = detection.get("posture", "unknown")
        mobility = detection.get("mobility", "unknown")
        environment = detection.get("environment", "open")

        score = 0
        breakdown = {}

        if det_type == "person":
            # --- Base person detection ---
            score += 20
            breakdown["person_base"] = 20

            if thermal_confirmed:
                score += 10
                breakdown["thermal_confirmation"] = 10

            if nearby_fire:
                score += 15
                breakdown["nearby_fire"] = 15

            if nearby_smoke:
                score += 5
                breakdown["nearby_smoke"] = 5

            if nearby_flood:
                score += 10
                breakdown["nearby_flood"] = 10

            if confidence >= 0.85:
                score += 5
                breakdown["high_confidence"] = 5

            # --- Health-based scoring ---
            if health_status == "CRITICAL":
                score += 20
                breakdown["health_critical"] = 20
            elif health_status == "INJURED":
                score += 10
                breakdown["health_injured"] = 10

            if posture in ("lying_down", "trapped"):
                score += 10
                breakdown["posture_risk"] = 10

            if mobility == "immobile":
                score += 10
                breakdown["immobile"] = 10

            if environment in ("near_fire", "in_water", "in_smoke"):
                score += 5
                breakdown["hazardous_environment"] = 5

        elif det_type == "fire":
            score = 80 if confidence >= 0.8 else 60
            breakdown["fire_hazard"] = score
        elif det_type == "flood":
            score = 70 if confidence >= 0.8 else 50
            breakdown["flood_hazard"] = score
        elif det_type == "smoke":
            score = 50 if confidence >= 0.8 else 30
            breakdown["smoke_hazard"] = score
        elif det_type == "damaged_structure":
            score = 65 if confidence >= 0.8 else 45
            breakdown["structure_hazard"] = score
        elif det_type == "debris":
            score = 40 if confidence >= 0.8 else 25
            breakdown["debris_hazard"] = score
        else:
            score = int(confidence * 40)
            breakdown["generic_detection"] = score

        # Cap at 100
        score = min(100, score)

        # Priority Level
        if score >= 81:
            priority = "CRITICAL"
        elif score >= 61:
            priority = "HIGH"
        elif score >= 31:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        return {
            "score": score,
            "priority": priority,
            "breakdown": breakdown,
            "factors": {
                "thermal_confirmed": thermal_confirmed,
                "nearby_fire": nearby_fire,
                "nearby_smoke": nearby_smoke,
                "nearby_flood": nearby_flood,
                "confidence": confidence,
                "health_status": health_status,
                "posture": posture,
                "mobility": mobility,
                "environment": environment
            }
        }
