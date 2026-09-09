import pytest
from ai.gps_simulator import GPSSimulator

def test_manual_flight_mode():
    sim = GPSSimulator(center_lat=11.0243, center_lon=76.9942)
    sim.set_flight_mode("MANUAL")
    assert sim.flight_mode == "MANUAL"
    
    # Apply movement vector (North)
    sim.apply_manual_command(vx=0.0, vy=10.0, vz=0.0)
    assert sim.manual_vy > 0
    
    # Step simulation
    telem = sim.step()
    assert telem["latitude"] > 11.0243
    assert len(telem["traversed_path"]) > 0
    assert telem["flight_mode"] == "MANUAL"

def test_autopilot_waypoints_navigation():
    sim = GPSSimulator(center_lat=11.0243, center_lon=76.9942)
    waypoints = [
        {"lat": 11.0250, "lon": 76.9950, "alt": 45.0},
        {"lat": 11.0260, "lon": 76.9960, "alt": 50.0},
    ]
    sim.set_predefined_path(waypoints, loop=True, auto_start=True)
    assert sim.flight_mode == "AUTOPILOT"
    assert len(sim.planned_path) == 2
    
    # Step simulation towards waypoint 1
    telem = sim.step()
    assert telem["current_waypoint_idx"] == 0
    assert telem["total_waypoints"] == 2
    assert len(telem["traversed_path"]) > 0

def test_clear_trail_and_rtl():
    sim = GPSSimulator(center_lat=11.0243, center_lon=76.9942)
    sim.apply_manual_command(vx=5.0, vy=5.0)
    sim.step()
    assert len(sim.traversed_path) > 0
    
    # Clear trail
    sim.clear_traversed_path()
    assert len(sim.traversed_path) <= 1
    
    # RTL
    sim.return_to_launch()
    assert sim.status == "RTL_RETURNING"
    assert sim.planned_path[0]["lat"] == 11.0243

def test_live_mobile_gps_path_tracking():
    sim = GPSSimulator(center_lat=11.0243, center_lon=76.9942)
    
    # Simulate moving with mobile camera across three coordinates
    sim.update_live_gps(lat=11.0245, lon=76.9945, altitude_m=48.0, speed_ms=1.2)
    sim.update_live_gps(lat=11.0248, lon=76.9949, altitude_m=49.0, speed_ms=1.5)
    sim.update_live_gps(lat=11.0252, lon=76.9953, altitude_m=50.0, speed_ms=1.4)
    
    telem = sim.get_telemetry()
    assert telem["gps_status"] == "LIVE_MOBILE_GPS"
    assert telem["latitude"] == 11.0252
    assert telem["longitude"] == 76.9953
    assert len(telem["traversed_path"]) >= 3

