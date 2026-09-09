import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polygon, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import ManualFlightHUD from './ManualFlightHUD';

/* ──── Smooth pan/recenter ──── */
function MapController({ center, zoom, forceZoom }) {
  const map = useMap();
  const prevCenter = useRef(null);
  useEffect(() => {
    if (!center || !center[0] || !center[1]) return;
    const same = prevCenter.current &&
      Math.abs(prevCenter.current[0] - center[0]) < 0.000001 &&
      Math.abs(prevCenter.current[1] - center[1]) < 0.000001;
    if (!same) {
      if (forceZoom) map.setView(center, zoom, { animate: true });
      else map.panTo(center, { animate: true, duration: 0.25, easeLinearity: 0.5 });
      prevCenter.current = center;
    }
  }, [center, zoom, forceZoom, map]);
  return null;
}


/* ──── Fly to searched location ──── */
function GoToLocation({ target }) {
  const map = useMap();
  useEffect(() => {
    if (!target) return;
    map.flyTo([target.lat, target.lon], 18, { duration: 1.5 });
  }, [target, map]);
  return null;
}

/* ──── Interactive Map Click Listener for Waypoint Drawing ──── */
function MapClickHandler({ isDrawing, onAddWaypoint }) {
  useMapEvents({
    click: (e) => {
      if (isDrawing && onAddWaypoint) {
        onAddWaypoint({ lat: e.latlng.lat, lon: e.latlng.lng, alt: 45.0 });
      }
    }
  });
  return null;
}

/* ──── Cardinal Directions Helper ──── */
function getCardinal(deg) {
  const normalized = ((deg % 360) + 360) % 360;
  if (normalized >= 337.5 || normalized < 22.5) return { label: 'NORTH', short: 'N', color: '#FF5252' };
  if (normalized >= 22.5 && normalized < 67.5) return { label: 'NORTH-EAST', short: 'NE', color: '#FF9100' };
  if (normalized >= 67.5 && normalized < 112.5) return { label: 'EAST', short: 'E', color: '#00E5FF' };
  if (normalized >= 112.5 && normalized < 157.5) return { label: 'SOUTH-EAST', short: 'SE', color: '#00E5FF' };
  if (normalized >= 157.5 && normalized < 202.5) return { label: 'SOUTH', short: 'S', color: '#7C8B96' };
  if (normalized >= 202.5 && normalized < 247.5) return { label: 'SOUTH-WEST', short: 'SW', color: '#7C8B96' };
  if (normalized >= 247.5 && normalized < 292.5) return { label: 'WEST', short: 'W', color: '#00E5FF' };
  return { label: 'NORTH-WEST', short: 'NW', color: '#FF9100' };
}

/* ──── Custom marker icons ──── */
function createCustomIcon(type, priority) {
  const isCritical = priority === 'CRITICAL';
  const configs = {
    person: { color: isCritical ? '#FF3B30' : '#4FD87A', emoji: isCritical ? '🆘' : '👤' },
    fire: { color: '#FF3D00', emoji: '🔥' },
    flood: { color: '#00B0FF', emoji: '🌊' },
    smoke: { color: '#B0BEC5', emoji: '💨' },
    debris: { color: '#FF9100', emoji: '🚧' },
    damaged_structure: { color: '#D500F9', emoji: '🏚️' },
  };
  const { color, emoji } = configs[type] || { color: '#2FD9C4', emoji: '📍' };
  const size = 32;
  const pulse = isCritical ? 'animation:pulse-ring 1.4s ease-out infinite;' : '';
  const html = `<div style="
    width:${size}px;height:${size}px;border-radius:50%;
    background:${color}25;border:2.5px solid ${color};
    display:flex;align-items:center;justify-content:center;
    font-size:15px;
    box-shadow:0 0 18px ${color}90,0 0 6px ${color}55;${pulse}
  ">${emoji}</div>`;
  return L.divIcon({ html, className: 'custom-leaflet-marker', iconSize: [size, size], iconAnchor: [size / 2, size / 2] });
}

/* ──── Rotating eVTOL Drone Marker with Cardinal Poles & Camera FOV ──── */
function createDroneMarkerIcon(headingDeg = 0, isManual = false, isLiveMobile = false) {
  const color = isLiveMobile ? '#00E5FF' : isManual ? '#FFC107' : '#2FD9C4';
  const cardinal = getCardinal(headingDeg);
  const size = 68;

  const html = `
    <div style="position:relative; width:${size}px; height:${size}px; display:flex; align-items:center; justify-content:center;">
      
      <!-- Static Cardinal Ring around the drone showing N/E/S/W poles -->
      <div style="
        position:absolute; width:64px; height:64px; border-radius:50%;
        border:1px dashed rgba(255,255,255,0.22);
        pointer-events:none;
      ">
        <span style="position:absolute; top:-4px; left:50%; transform:translateX(-50%); font-size:8px; font-weight:900; color:#FF5252; font-family:monospace;">N</span>
        <span style="position:absolute; right:1px; top:50%; transform:translateY(-50%); font-size:8px; font-weight:900; color:#00E5FF; font-family:monospace;">E</span>
        <span style="position:absolute; bottom:-4px; left:50%; transform:translateX(-50%); font-size:8px; font-weight:900; color:#7C8B96; font-family:monospace;">S</span>
        <span style="position:absolute; left:1px; top:50%; transform:translateY(-50%); font-size:8px; font-weight:900; color:#00E5FF; font-family:monospace;">W</span>
      </div>

      <!-- Rotating Drone Body & Forward Camera Beam -->
      <div style="
        position:absolute; width:100%; height:100%;
        display:flex; align-items:center; justify-content:center;
        transform: rotate(${headingDeg}deg);
        transition: transform 0.22s cubic-bezier(0.2, 0, 0.4, 1);
      ">
        <!-- Forward Camera Field-of-View Cone -->
        <div style="
          position:absolute; top:2px;
          width:0; height:0;
          border-left:14px solid transparent;
          border-right:14px solid transparent;
          border-top:28px solid ${color}40;
          filter: drop-shadow(0 0 6px ${color}80);
          pointer-events:none;
        "></div>

        <!-- Forward Heading Pointer Arrow -->
        <div style="
          position:absolute; top:3px;
          width:0; height:0;
          border-left:4px solid transparent;
          border-right:4px solid transparent;
          border-bottom:7px solid ${color};
          transform:rotate(180deg);
        "></div>

        <!-- Drone Center Body -->
        <div style="
          width:36px; height:36px; border-radius:50%;
          background:rgba(10,15,20,0.92); border:2.5px solid ${color};
          display:flex; align-items:center; justify-content:center;
          box-shadow:0 0 16px ${color}95, inset 0 0 8px ${color}40;
          font-size:16px;
        ">
          ${isLiveMobile ? '📱' : '🛸'}
        </div>
      </div>

      <!-- Live Heading & Pole Badge -->
      <div style="
        position:absolute; bottom:-12px; left:50%; transform:translateX(-50%);
        background:rgba(10,15,20,0.92); border:1px solid ${color}80;
        border-radius:3px; padding:1px 5px; font-size:8px; font-weight:800;
        color:${color}; font-family:monospace; white-space:nowrap;
        box-shadow:0 2px 8px rgba(0,0,0,0.8);
      ">
        ${Math.round(headingDeg)}° ${cardinal.short}
      </div>
    </div>
  `;

  return L.divIcon({
    html,
    className: 'custom-leaflet-marker',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
}


/* ──── Waypoint marker icon ──── */
function createWaypointIcon(index, isActive) {
  const color = isActive ? '#FFD700' : '#00E5FF';
  const html = `<div style="
    width:26px;height:26px;border-radius:50%;
    background:rgba(10,15,20,0.9);border:2px solid ${color};
    display:flex;align-items:center;justify-content:center;
    font-size:10px;font-weight:900;font-family:monospace;color:${color};
    box-shadow:0 0 10px ${color}99;
    ${isActive ? 'transform:scale(1.25);animation:pulse-ring 1.2s infinite;' : ''}
  ">W${index + 1}</div>`;
  return L.divIcon({ html, className: 'custom-leaflet-marker', iconSize: [26, 26], iconAnchor: [13, 13] });
}

/* ──── Zone colours ──── */
const ZONE_COLORS = {
  fire: { color: '#FF3D00', fillColor: '#8B0000', fillOpacity: 0.42, weight: 2.5, dashArray: '6,3' },
  flood: { color: '#00B0FF', fillColor: '#003366', fillOpacity: 0.36, weight: 2, dashArray: '6,3' },
  landslide: { color: '#8B4513', fillColor: '#5C3317', fillOpacity: 0.40, weight: 2.5, dashArray: '6,3' },
  earthquake: { color: '#FF9100', fillColor: '#8B4500', fillOpacity: 0.36, weight: 2, dashArray: '6,3' },
};

/* ──────────────────────────────────────────────────────── */
export default function DisasterMap({
  detections = [],
  zones = [],
  telemetry,
  selectedDetection,
  onSelectDetection,
  missionPhase,
  onManualCommand,
  onSetFlightMode,
  onSetWaypoints,
  onClearTrail,
  onRTL
}) {
  const DEFAULT_LAT = 11.0243;
  const DEFAULT_LON = 76.9942;
  const DEFAULT_ZOOM = 18;

  const droneLat = telemetry?.latitude || DEFAULT_LAT;
  const droneLon = telemetry?.longitude || DEFAULT_LON;
  const flightMode = telemetry?.flight_mode || 'AUTOPILOT';
  const traversedPath = telemetry?.traversed_path || [];
  const plannedPath = telemetry?.planned_path || [];
  const currentWpIdx = telemetry?.current_waypoint_idx || 0;

  const [searchText, setSearchText] = useState('SREC Coimbatore');
  const [searching, setSearching] = useState(false);
  const [searchErr, setSearchErr] = useState('');
  const [gotoTarget, setGotoTarget] = useState(null);
  const [followDrone, setFollowDrone] = useState(false);
  const [satellite, setSatellite] = useState(false);

  // Live Mobile GPS Tracking
  const [mobileGpsActive, setMobileGpsActive] = useState(false);
  const [gpsAccuracy, setGpsAccuracy] = useState(null);
  const [watchId, setWatchId] = useState(null);

  const toggleMobileGPS = useCallback(() => {
    if (mobileGpsActive) {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
        setWatchId(null);
      }
      setMobileGpsActive(false);
      setGpsAccuracy(null);
    } else {
      if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser.');
        return;
      }
      const id = navigator.geolocation.watchPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const alt = pos.coords.altitude || 45.0;
          const speed = pos.coords.speed || 0.0;
          const heading = pos.coords.heading || null;
          const accuracy = pos.coords.accuracy ? Math.round(pos.coords.accuracy) : null;
          setGpsAccuracy(accuracy);

          fetch('http://localhost:8000/api/drone/mobile_gps', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              lat,
              lon,
              altitude_m: alt,
              speed_ms: speed,
              heading_deg: heading,
              accuracy_m: accuracy
            })
          }).catch(console.error);
        },
        (err) => {
          console.warn('Mobile GPS error:', err.message);
        },
        {
          enableHighAccuracy: true,
          maximumAge: 0,
          timeout: 8000
        }
      );
      setWatchId(id);
      setMobileGpsActive(true);
      setFollowDrone(true);

    }
  }, [mobileGpsActive, watchId]);

  useEffect(() => {
    return () => {
      if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
      }
    };
  }, [watchId]);

  // Mobile Compass / Device Orientation Listener (Syncs mobile rotation with drone & compass)
  useEffect(() => {
    let lastSent = 0;
    const handleOrientation = (e) => {
      let compass = null;
      if (e.webkitCompassHeading !== undefined && e.webkitCompassHeading !== null) {
        compass = e.webkitCompassHeading; // iOS True Compass
      } else if (e.alpha !== null && e.alpha !== undefined) {
        compass = (360 - e.alpha) % 360; // Android absolute azimuth
      }
      if (compass !== null && !isNaN(compass)) {
        const now = Date.now();
        if (now - lastSent > 120) {
          lastSent = now;
          fetch('http://localhost:8000/api/drone/mobile_gps', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              lat: droneLat,
              lon: droneLon,
              altitude_m: telemetry?.altitude_m || 45.0,
              speed_ms: telemetry?.speed_ms || 0.0,
              heading_deg: compass
            })
          }).catch(() => {});
        }
      }
    };

    window.addEventListener('deviceorientationabsolute', handleOrientation, true);
    window.addEventListener('deviceorientation', handleOrientation, true);
    return () => {
      window.removeEventListener('deviceorientationabsolute', handleOrientation, true);
      window.removeEventListener('deviceorientation', handleOrientation, true);
    };
  }, [droneLat, droneLon, telemetry?.altitude_m, telemetry?.speed_ms]);


  // Waypoint Path Planner State
  const [isDrawingPath, setIsDrawingPath] = useState(false);
  const [localWaypoints, setLocalWaypoints] = useState([]);



  // Sync planned path into local state when incoming
  useEffect(() => {
    if (plannedPath && plannedPath.length > 0 && !isDrawingPath) {
      setLocalWaypoints(plannedPath);
    }
  }, [plannedPath, isDrawingPath]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchText.trim()) return;
    setSearching(true);
    setSearchErr('');
    try {
      const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchText)}&format=json&limit=1`;
      const res = await fetch(url, { headers: { 'User-Agent': 'RescueVisionAI/1.0' } });
      const data = await res.json();
      if (!data.length) {
        setSearchErr('Location not found — try a more specific name.');
      } else {
        const lat = parseFloat(data[0].lat);
        const lon = parseFloat(data[0].lon);
        setGotoTarget({ lat, lon, name: data[0].display_name });
        setFollowDrone(false);
      }
    } catch {
      setSearchErr('Search failed. Check your connection.');
    } finally {
      setSearching(false);
    }
  };

  const handleAddWaypoint = (wp) => {
    setLocalWaypoints(prev => [...prev, wp]);
  };

  const handleClearWaypoints = async () => {
    setLocalWaypoints([]);
    setIsDrawingPath(false);
    try {
      await fetch('http://localhost:8000/api/drone/clear_waypoints', { method: 'POST' });
    } catch (err) {
      console.error(err);
    }
  };

  const handleExecutePath = async () => {
    if (localWaypoints.length < 2) {
      alert('Please add at least 2 waypoints on the map to define a path.');
      return;
    }
    try {
      const res = await fetch('http://localhost:8000/api/drone/waypoints', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          waypoints: localWaypoints,
          loop: true,
          auto_start: true
        })
      });
      if (res.ok) {
        setIsDrawingPath(false);
        if (onSetFlightMode) onSetFlightMode('AUTOPILOT');
      }
    } catch (err) {
      console.error('Execute path failed', err);
    }
  };

  // Generate an automated Lawnmower Grid Survey around current coordinates
  const handleGenerateGridScan = () => {
    const baseLat = droneLat;
    const baseLon = droneLon;
    const step = 0.0006; // ~65 meters

    const grid = [
      { lat: baseLat - step, lon: baseLon - step, alt: 45.0 },
      { lat: baseLat + step, lon: baseLon - step, alt: 45.0 },
      { lat: baseLat + step, lon: baseLon, alt: 45.0 },
      { lat: baseLat - step, lon: baseLon, alt: 45.0 },
      { lat: baseLat - step, lon: baseLon + step, alt: 45.0 },
      { lat: baseLat + step, lon: baseLon + step, alt: 45.0 },
    ];
    setLocalWaypoints(grid);
  };

  // Generate a rectangular Perimeter Sweep
  const handleGeneratePerimeterScan = () => {
    const baseLat = droneLat;
    const baseLon = droneLon;
    const r = 0.0009; // ~100 meters
    const perimeter = [
      { lat: baseLat + r, lon: baseLon - r, alt: 50.0 },
      { lat: baseLat + r, lon: baseLon + r, alt: 50.0 },
      { lat: baseLat - r, lon: baseLon + r, alt: 50.0 },
      { lat: baseLat - r, lon: baseLon - r, alt: 50.0 },
    ];
    setLocalWaypoints(perimeter);
  };

  // Effective waypoints to render
  const waypointsToDisplay = isDrawingPath || localWaypoints.length > 0 ? localWaypoints : plannedPath;
  const plannedPositions = waypointsToDisplay.map(w => [w.lat, w.lon]);

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative', overflow: 'hidden', borderRadius: '8px' }}>

      {/* ── Search bar ── */}
      <div style={{
        position: 'absolute', top: '10px', left: '50%', transform: 'translateX(-50%)',
        zIndex: 1000, display: 'flex', gap: '6px', width: 'min(92%, 440px)',
      }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '6px', width: '100%' }}>
          <input
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            placeholder="Campus / building / location…"
            style={{
              flex: 1, padding: '7px 11px', borderRadius: '6px',
              border: '1px solid rgba(47,217,196,0.4)',
              background: 'rgba(10,15,20,0.9)', color: '#DCE6EC',
              fontSize: '12px', fontFamily: 'monospace',
              backdropFilter: 'blur(8px)', outline: 'none',
              boxShadow: '0 2px 12px rgba(0,0,0,0.55)',
            }}
          />
          <button
            type="submit" disabled={searching}
            style={{
              padding: '7px 13px', borderRadius: '6px',
              border: '1px solid rgba(47,217,196,0.5)',
              background: searching ? 'rgba(47,217,196,0.08)' : 'rgba(47,217,196,0.18)',
              color: '#2FD9C4', fontSize: '12px', fontFamily: 'monospace',
              cursor: searching ? 'not-allowed' : 'pointer',
              fontWeight: 700, letterSpacing: '0.5px',
            }}
          >{searching ? '…' : '📡 GO'}</button>
        </form>
        {searchErr && (
          <div style={{
            position: 'absolute', top: '100%', left: 0, marginTop: '4px',
            background: 'rgba(255,90,82,0.92)', color: '#fff',
            padding: '5px 10px', borderRadius: '5px', fontSize: '11px', whiteSpace: 'nowrap',
          }}>{searchErr}</div>
        )}
      </div>

      {/* ── Top-Right Map Controls ── */}
      <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 1000, display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <button
          onClick={() => setSatellite(s => !s)}
          style={mapCtrlBtn(satellite)}
          title="Toggle Satellite Imagery"
        >{satellite ? '🗺' : '🛰'}</button>

        <button
          onClick={() => setFollowDrone(f => !f)}
          style={mapCtrlBtn(followDrone)}
          title="Follow Drone"
        >🛸</button>

        <button
          onClick={toggleMobileGPS}
          style={{
            ...mapCtrlBtn(mobileGpsActive),
            background: mobileGpsActive ? 'rgba(0, 229, 255, 0.35)' : 'rgba(10,15,20,0.88)',
            color: mobileGpsActive ? '#00E5FF' : '#7C8B96',
            borderColor: mobileGpsActive ? '#00E5FF' : 'rgba(47,217,196,0.3)',
            boxShadow: mobileGpsActive ? '0 0 12px rgba(0,229,255,0.6)' : 'none'
          }}
          title={mobileGpsActive ? "Tracking Phone Live GPS (Click to stop)" : "Track Moving Phone / Mobile Camera GPS"}
        >📱</button>

        <button
          onClick={() => onSetFlightMode && onSetFlightMode(flightMode === 'MANUAL' ? 'AUTOPILOT' : 'MANUAL')}
          style={{
            ...mapCtrlBtn(flightMode === 'MANUAL'),
            color: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4',
            borderColor: flightMode === 'MANUAL' ? '#FFC107' : 'rgba(47,217,196,0.3)',
            fontSize: '10px',
            fontWeight: 800,
            padding: '5px 6px'
          }}
          title="Toggle Flight Mode"
        >
          {flightMode === 'MANUAL' ? '🕹️' : '🤖'}
        </button>
      </div>

      {/* ── Live Mobile Tracking Badge ── */}
      {(mobileGpsActive || telemetry?.gps_status === 'LIVE_MOBILE_GPS') && (
        <div style={{
          position: 'absolute',
          top: '52px',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 1000,
          background: 'rgba(0, 229, 255, 0.2)',
          border: '1px solid #00E5FF',
          backdropFilter: 'blur(8px)',
          borderRadius: '20px',
          padding: '3px 12px',
          fontSize: '10px',
          fontWeight: 800,
          color: '#00E5FF',
          fontFamily: 'monospace',
          letterSpacing: '0.5px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          boxShadow: '0 0 15px rgba(0, 229, 255, 0.4)'
        }}>
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#00E5FF', animation: 'pulse-ring 1s infinite' }}></span>
          <span>LIVE MOBILE CAMERA GPS · {gpsAccuracy ? `±${gpsAccuracy}m` : 'CONNECTED'}</span>
        </div>
      )}

      {/* ── Tactical Polar Compass Rose HUD (North / East / South / West) ── */}
      <div style={{
        position: 'absolute',
        top: '148px',
        right: '10px',
        zIndex: 1000,
        background: 'rgba(8, 14, 20, 0.94)',
        backdropFilter: 'blur(12px)',
        border: '1.5px solid rgba(47, 217, 196, 0.45)',
        borderRadius: '50%',
        width: '74px',
        height: '74px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: '0 6px 20px rgba(0,0,0,0.75), 0 0 12px rgba(47,217,196,0.2)',
        userSelect: 'none'
      }}>
        {/* Fixed Outer Cardinal Labels */}
        <span style={{ position: 'absolute', top: '2px', fontSize: '9px', fontWeight: 900, color: '#FF5252', fontFamily: 'monospace' }}>N</span>
        <span style={{ position: 'absolute', right: '4px', fontSize: '9px', fontWeight: 900, color: '#00E5FF', fontFamily: 'monospace' }}>E</span>
        <span style={{ position: 'absolute', bottom: '2px', fontSize: '9px', fontWeight: 900, color: '#7C8B96', fontFamily: 'monospace' }}>S</span>
        <span style={{ position: 'absolute', left: '4px', fontSize: '9px', fontWeight: 900, color: '#00E5FF', fontFamily: 'monospace' }}>W</span>

        {/* Rotating Heading Needle Dial */}
        <div style={{
          width: '100%',
          height: '100%',
          position: 'absolute',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `rotate(${telemetry?.heading_deg || 0}deg)`,
          transition: 'transform 0.22s cubic-bezier(0.2, 0, 0.4, 1)'
        }}>
          {/* North pointing Red Pointer */}
          <div style={{
            position: 'absolute',
            top: '14px',
            width: 0,
            height: 0,
            borderLeft: '4px solid transparent',
            borderRight: '4px solid transparent',
            borderBottom: '16px solid #FF5252'
          }}></div>
          {/* South pointing Muted Pointer */}
          <div style={{
            position: 'absolute',
            bottom: '14px',
            width: 0,
            height: 0,
            borderLeft: '4px solid transparent',
            borderRight: '4px solid transparent',
            borderTop: '16px solid rgba(220, 230, 236, 0.35)'
          }}></div>
        </div>

        {/* Center Pivot with Active Direction Readout */}
        <div style={{
          width: '26px',
          height: '26px',
          borderRadius: '50%',
          background: '#070B0E',
          border: '1.5px solid #2FD9C4',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2,
          boxShadow: '0 0 8px rgba(47,217,196,0.4)'
        }}>
          <span style={{ fontSize: '8px', fontWeight: 900, color: '#2FD9C4', fontFamily: 'monospace', lineHeight: 1 }}>
            {getCardinal(telemetry?.heading_deg || 0).short}
          </span>
          <span style={{ fontSize: '6px', color: '#7C8B96', fontFamily: 'monospace', lineHeight: 1 }}>
            {Math.round(telemetry?.heading_deg || 0)}°
          </span>
        </div>
      </div>



      {/* ── Path Planner Toolbar (Top Left) ── */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 1000,
        background: 'rgba(10, 15, 20, 0.90)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(47, 217, 196, 0.35)',
        borderRadius: '8px',
        padding: '6px 8px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        fontSize: '11px',
        fontFamily: 'var(--mono, monospace)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.6)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
          <span style={{ fontWeight: 800, color: '#2FD9C4', fontSize: '10px' }}>
            📍 TACTICAL PATH
          </span>
          <span style={{ fontSize: '9px', color: '#7C8B96' }}>
            {waypointsToDisplay.length} WPs
          </span>
        </div>

        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          <button
            onClick={() => setIsDrawingPath(d => !d)}
            style={{
              padding: '4px 7px',
              borderRadius: '5px',
              background: isDrawingPath ? 'rgba(0, 229, 255, 0.3)' : 'rgba(255,255,255,0.06)',
              border: `1px solid ${isDrawingPath ? '#00E5FF' : 'rgba(255,255,255,0.15)'}`,
              color: isDrawingPath ? '#00E5FF' : '#DCE6EC',
              cursor: 'pointer',
              fontSize: '10px',
              fontWeight: 700
            }}
          >
            {isDrawingPath ? '✏️ CLICK TO ADD' : '✏️ DRAW PATH'}
          </button>

          <button
            onClick={handleGenerateGridScan}
            style={pathActionBtn}
            title="Auto-generate Lawnmower Grid Scan"
          >
            📐 GRID
          </button>

          <button
            onClick={handleGeneratePerimeterScan}
            style={pathActionBtn}
            title="Auto-generate Perimeter Outline"
          >
            🔲 PERIMETER
          </button>
        </div>

        {waypointsToDisplay.length > 0 && (
          <div style={{ display: 'flex', gap: '4px', marginTop: '2px' }}>
            <button
              onClick={handleExecutePath}
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, rgba(47,217,196,0.35), rgba(0,229,255,0.35))',
                border: '1px solid #2FD9C4',
                color: '#2FD9C4',
                borderRadius: '4px',
                padding: '4px 6px',
                fontSize: '10px',
                fontWeight: 800,
                cursor: 'pointer'
              }}
            >
              🚀 EXECUTE PATH
            </button>
            <button
              onClick={handleClearWaypoints}
              style={{
                background: 'rgba(255,90,82,0.15)',
                border: '1px solid rgba(255,90,82,0.3)',
                color: '#FF5A52',
                borderRadius: '4px',
                padding: '4px 6px',
                fontSize: '10px',
                cursor: 'pointer'
              }}
              title="Clear Waypoint Plan"
            >
              🗑️
            </button>
          </div>
        )}
      </div>

      {/* ── Map Container ── */}
      <MapContainer
        center={[DEFAULT_LAT, DEFAULT_LON]}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        zoomControl={false}
        style={{ height: '100%', width: '100%', background: '#0A0F14', cursor: isDrawingPath ? 'crosshair' : 'grab' }}
        maxZoom={19}
      >
        {/* Tile Layer */}
        {satellite ? (
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution='Tiles &copy; Esri'
            maxZoom={19}
            maxNativeZoom={18}
          />
        ) : (
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            maxZoom={19}
          />
        )}

        {/* Map Click Listener for Waypoints */}
        <MapClickHandler isDrawing={isDrawingPath} onAddWaypoint={handleAddWaypoint} />

        {/* Geocode fly-to */}
        {gotoTarget && <GoToLocation target={gotoTarget} />}

        {/* Follow drone */}
        {followDrone && <MapController center={[droneLat, droneLon]} zoom={18} forceZoom={false} />}

        {/* ── Traversed Flight Trail (Outlined Breadcrumbs) ── */}
        {traversedPath.length > 1 && (
          <>
            {/* Outer soft glow */}
            <Polyline
              positions={traversedPath}
              pathOptions={{
                color: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4',
                weight: 6,
                opacity: 0.35,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
            {/* Core sharp flight path */}
            <Polyline
              positions={traversedPath}
              pathOptions={{
                color: flightMode === 'MANUAL' ? '#FFE082' : '#E0F7FA',
                weight: 2.5,
                opacity: 0.95,
                lineCap: 'round',
                lineJoin: 'round'
              }}
            />
          </>
        )}

        {/* ── Planned / Designated Autopilot Waypoints Path ── */}
        {plannedPositions.length > 1 && (
          <Polyline
            positions={plannedPositions}
            pathOptions={{
              color: '#00E5FF',
              weight: 2.5,
              dashArray: '6,6',
              opacity: 0.85
            }}
          />
        )}

        {/* Waypoint Markers */}
        {waypointsToDisplay.map((wp, idx) => (
          <Marker
            key={`wp-${idx}-${wp.lat}-${wp.lon}`}
            position={[wp.lat, wp.lon]}
            icon={createWaypointIcon(idx, idx === currentWpIdx && flightMode === 'AUTOPILOT')}
          >
            <Popup>
              <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', lineHeight: 1.5 }}>
                <strong style={{ color: '#00E5FF' }}>WAYPOINT #{idx + 1}</strong><br />
                Target Alt: {wp.alt || 45}m<br />
                📍 {wp.lat.toFixed(6)}, {wp.lon.toFixed(6)}
              </div>
            </Popup>
          </Marker>
        ))}

        {/* ── Disaster Zone Polygons ── */}
        {zones.map((zone, idx) => {
          const polygon = zone.boundary_polygon;
          if (!polygon || polygon.length < 3) return null;
          const style = ZONE_COLORS[zone.disaster_type] || ZONE_COLORS.fire;
          return (
            <Polygon key={zone.zone_id || `z-${idx}`} positions={polygon} pathOptions={style}>
              <Popup>
                <div style={{ fontFamily: 'monospace', fontSize: '0.78rem', lineHeight: 1.6 }}>
                  <strong style={{ color: '#FF3D00' }}>🔥 {zone.zone_id}</strong><br />
                  Type: {zone.disaster_type?.toUpperCase()}<br />
                  Severity: <strong>{zone.severity}</strong><br />
                  Area: {zone.area_sq_meters?.toFixed(0)} m²<br />
                  Coverage: {zone.coverage_pct}%
                </div>
              </Popup>
            </Polygon>
          );
        })}

        {/* ── eVTOL Drone Marker ── */}
        <Marker
          position={[droneLat, droneLon]}
          icon={createDroneMarkerIcon(
            telemetry?.heading_deg || 0,
            flightMode === 'MANUAL',
            mobileGpsActive || telemetry?.gps_status === 'LIVE_MOBILE_GPS'
          )}
        >

          <Popup>
            <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', lineHeight: 1.6 }}>
              <strong>🛸 eVTOL RECON DRONE</strong><br />
              Mode: <strong style={{ color: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4' }}>{flightMode}</strong><br />
              Phase: {missionPhase || 'SURVEY'}<br />
              Status: {telemetry?.mission_status || 'STANDBY'}<br />
              Alt: {telemetry?.altitude_m || 45}m | Speed: {telemetry?.speed_ms || 0} m/s<br />
              Batt: {telemetry?.battery_pct || 94}% | Heading: {telemetry?.heading_deg || 0}°<br />
              📍 {droneLat.toFixed(5)}, {droneLon.toFixed(5)}
            </div>
          </Popup>
        </Marker>

        {/* Scan sweep circle */}
        <Circle
          center={[droneLat, droneLon]}
          radius={80}
          pathOptions={{
            color: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4',
            fillColor: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4',
            fillOpacity: 0.06,
            weight: 1.5,
            dashArray: '4,4'
          }}
        />

        {/* ── Detection Markers ── */}
        {detections.map(det => (
          <Marker
            key={det.id}
            position={[det.latitude, det.longitude]}
            icon={createCustomIcon(det.type, det.priority)}
            eventHandlers={{ click: () => onSelectDetection && onSelectDetection(det) }}
          >
            <Popup>
              <div style={{ fontFamily: 'monospace', fontSize: '0.78rem', lineHeight: 1.6 }}>
                <strong style={{ color: det.priority === 'CRITICAL' ? '#FF5A52' : '#2FD9C4' }}>
                  {det.id} ({det.type.toUpperCase()})
                </strong><br />
                Priority: <strong>{det.priority}</strong> · Risk: {det.risk_score}/100<br />
                Confidence: {(det.confidence * 100).toFixed(0)}%<br />
                {det.type === 'person' && <>
                  Health: <strong>{det.health_status || '—'}</strong><br />
                  Posture: {det.posture || '—'} | Mobility: {det.mobility || '—'}<br />
                </>}
                Thermal: {det.thermal_confirmed ? '✅ YES' : '❌ NO'}<br />
                📍 {det.latitude.toFixed(5)}, {det.longitude.toFixed(5)}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* ── Manual Flight HUD (Overlay when in MANUAL mode) ── */}
      <ManualFlightHUD
        flightMode={flightMode}
        onManualCommand={onManualCommand}
        onSetFlightMode={onSetFlightMode}
        onRTL={onRTL}
        onClearTrail={onClearTrail}
      />

      {/* ── Legend ── */}
      <div style={{
        position: 'absolute', bottom: '10px', left: '10px', zIndex: 1000,
        background: 'rgba(10,15,20,0.88)', backdropFilter: 'blur(8px)',
        border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px',
        padding: '6px 10px', display: 'flex', gap: '9px', flexWrap: 'wrap',
        fontSize: '0.67rem', color: 'rgba(220,230,236,0.75)',
      }}>
        <span>🛸 Drone</span>
        <span style={{ color: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4' }}>
          ━ {flightMode === 'MANUAL' ? 'Manual Trail' : 'Flight Trail'}
        </span>
        <span style={{ color: '#00E5FF' }}>┄ Planned Path</span>
        <span>👤 Survivor</span><span>🆘 Critical</span>
        <span>🔥 Fire</span><span>🌊 Flood</span>
      </div>

      {/* ── Flight Mode & Phase Badges ── */}
      <div style={{
        position: 'absolute', bottom: '10px', right: '10px', zIndex: 1000,
        display: 'flex', gap: '6px'
      }}>
        <div style={{
          background: flightMode === 'MANUAL' ? 'rgba(255,193,7,0.2)' : 'rgba(47,217,196,0.2)',
          border: `1px solid ${flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4'}`,
          backdropFilter: 'blur(8px)', borderRadius: '6px', padding: '5px 10px',
          fontSize: '0.72rem', fontWeight: 800,
          color: flightMode === 'MANUAL' ? '#FFC107' : '#2FD9C4',
          fontFamily: 'monospace', letterSpacing: '0.5px',
        }}>
          {flightMode === 'MANUAL' ? '🕹️ MANUAL' : '🤖 AUTOPILOT'}
        </div>

        <div style={{
          background: missionPhase === 'SAR' ? 'rgba(255,59,48,0.85)' : 'rgba(47,217,196,0.15)',
          border: `1px solid ${missionPhase === 'SAR' ? '#FF5A52' : '#2FD9C4'}`,
          backdropFilter: 'blur(8px)', borderRadius: '6px', padding: '5px 10px',
          fontSize: '0.72rem', fontWeight: 800,
          color: missionPhase === 'SAR' ? '#fff' : '#2FD9C4',
          fontFamily: 'monospace', letterSpacing: '0.5px',
        }}>
          {missionPhase === 'SAR' ? '🔍 SAR' : '📡 SURVEY'}
        </div>
      </div>

      {/* ── Location name pill ── */}
      {gotoTarget && (
        <div style={{
          position: 'absolute', top: '50px', left: '50%', transform: 'translateX(-50%)',
          zIndex: 1000, background: 'rgba(10,15,20,0.90)', backdropFilter: 'blur(8px)',
          border: '1px solid rgba(47,217,196,0.3)', borderRadius: '5px',
          padding: '4px 12px', fontSize: '10px', color: '#7C8B96',
          fontFamily: 'monospace', maxWidth: '90%',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>📍 {gotoTarget.name}</div>
      )}
    </div>
  );
}

function mapCtrlBtn(active) {
  return {
    background: active ? 'rgba(47,217,196,0.28)' : 'rgba(10,15,20,0.88)',
    border: `1px solid ${active ? '#2FD9C4' : 'rgba(47,217,196,0.3)'}`,
    color: active ? '#2FD9C4' : '#7C8B96',
    borderRadius: '6px',
    padding: '5px 9px',
    fontSize: '11px',
    cursor: 'pointer',
    fontFamily: 'monospace',
    backdropFilter: 'blur(8px)',
  };
}

const pathActionBtn = {
  padding: '4px 7px',
  borderRadius: '5px',
  background: 'rgba(255,255,255,0.06)',
  border: '1px solid rgba(255,255,255,0.15)',
  color: '#DCE6EC',
  cursor: 'pointer',
  fontSize: '10px',
  fontWeight: 700
};
