"""
Unit Tests for Risk Engine, Spatial Tracker, and Health Classifier.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.risk_engine import RiskEngine
from ai.tracker import DetectionTracker, haversine_distance_meters
from ai.health import HealthClassifier


# ──────────────── Risk Engine Tests ────────────────

def test_critical_survivor_with_health():
    engine = RiskEngine()
    
    detection = {
        "type": "person",
        "confidence": 0.94,
        "thermal_confirmed": True,
        "nearby_fire": True,
        "nearby_smoke": False,
        "health_status": "CRITICAL",
        "posture": "lying_down",
        "mobility": "immobile",
        "environment": "near_fire"
    }
    
    res = engine.calculate_risk(detection)
    # 20(person) + 10(thermal) + 15(fire) + 5(conf) + 20(health_crit) + 10(posture) + 10(immobile) + 5(env) = 95
    assert res["score"] == 95
    assert res["priority"] == "CRITICAL"


def test_stable_survivor_scoring():
    engine = RiskEngine()
    
    detection = {
        "type": "person",
        "confidence": 0.80,
        "thermal_confirmed": True,
        "nearby_fire": False,
        "nearby_smoke": False,
        "health_status": "STABLE",
        "posture": "standing",
        "mobility": "mobile",
        "environment": "open"
    }
    
    res = engine.calculate_risk(detection)
    # 20(person) + 10(thermal) = 30 → LOW
    assert res["score"] == 30
    assert res["priority"] == "LOW"


def test_fire_hazard_scoring():
    engine = RiskEngine()
    detection = {"type": "fire", "confidence": 0.89}
    res = engine.calculate_risk(detection)
    assert res["score"] == 80
    assert res["priority"] == "HIGH"


# ──────────────── Spatial Tracker Tests ────────────────

def test_haversine_distance():
    dist = haversine_distance_meters(11.0168, 76.9558, 11.0172, 76.9563)
    assert 50.0 <= dist <= 90.0


def test_tracker_proximity_assignment():
    tracker = DetectionTracker(proximity_threshold_m=100.0)
    
    dets = [
        {"id": "SURVIVOR_001", "type": "person", "latitude": 11.0168, "longitude": 76.9558},
        {"id": "FIRE_001", "type": "fire", "latitude": 11.0172, "longitude": 76.9563}
    ]
    
    updated = tracker.update_spatial_relationships(dets)
    person_det = [d for d in updated if d["type"] == "person"][0]
    assert person_det["nearby_fire"] is True


# ──────────────── Health Classifier Tests ────────────────

def test_health_lying_immobile_fire():
    classifier = HealthClassifier()
    
    detection = {
        "id": "SURVIVOR_001",
        "type": "person",
        "latitude": 11.0168,
        "longitude": 76.9558,
        "nearby_fire": True,
        "nearby_flood": False,
        "nearby_smoke": False
    }
    
    # Wide bounding box → lying down
    bbox = [100, 200, 400, 280]  # width=300, height=80 → aspect < 0.4 → lying
    
    result = classifier.classify(detection, bbox=bbox)
    assert result["posture"] == "lying_down"
    assert result["environment"] == "near_fire"
    assert result["health_status"] == "CRITICAL"


def test_health_standing_open():
    classifier = HealthClassifier()
    
    detection = {
        "id": "SURVIVOR_002",
        "type": "person",
        "latitude": 11.0195,
        "longitude": 76.9520,
        "nearby_fire": False,
        "nearby_flood": False,
        "nearby_smoke": False
    }
    
    # Tall narrow bounding box → standing
    bbox = [100, 100, 160, 400]  # width=60, height=300 → aspect=5 → standing
    
    result = classifier.classify(detection, bbox=bbox)
    assert result["posture"] == "standing"
    assert result["environment"] == "open"
    assert result["health_status"] == "STABLE"


def test_health_non_person():
    classifier = HealthClassifier()
    detection = {"id": "FIRE_001", "type": "fire", "latitude": 11.0172, "longitude": 76.9563}
    result = classifier.classify(detection)
    assert result["health_status"] == "N/A"
