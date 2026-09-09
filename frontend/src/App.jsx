import React, { useState, useEffect, useRef } from 'react';
import DisasterMap from './components/DisasterMap';
import MissionControls from './components/MissionControls';
import DetectionSummary from './components/DetectionSummary';
import AIInsights from './components/AIInsights';

export default function App() {
  const [telemetry, setTelemetry] = useState({
    drone_active: false,
    ai_active: false,
    mission_status: "STANDBY",
    flight_mode: "AUTOPILOT",
    gps_status: "SIMULATED",
    network_status: "ONLINE",
    latitude: 11.0195,
    longitude: 76.9561,
    altitude_m: 45.0,
    speed_ms: 6.5,
    battery_pct: 100.0,
    sector: "Riverside",
    camera_source: "none",
    camera_active: false,
    traversed_path: [],
    planned_path: [],
    current_waypoint_idx: 0
  });

  const [detections, setDetections] = useState([]);
  const [zones, setZones] = useState([]);
  const [stats, setStats] = useState({});
  const [wsConnected, setWsConnected] = useState(false);
  const [missionPhase, setMissionPhase] = useState('SURVEY');
  const [selectedDetection, setSelectedDetection] = useState(null);
  
  const wsRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const connectWebSocket = () => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/live');

    wsRef.current.onopen = () => {
      setWsConnected(true);
      console.log('WS Connected');
    };

    wsRef.current.onclose = () => {
      setWsConnected(false);
      setTimeout(connectWebSocket, 2000);
    };

    wsRef.current.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'FULL_STATE' || msg.type === 'TELEMETRY_UPDATE') {
          if (msg.data.telemetry) setTelemetry(msg.data.telemetry);
          if (msg.data.detections) setDetections(msg.data.detections);
          if (msg.data.zones) setZones(msg.data.zones);
          if (msg.data.stats) setStats(msg.data.stats);
          if (msg.data.telemetry?.mission_phase) setMissionPhase(msg.data.telemetry.mission_phase);
        } else if (msg.type === 'telemetry') {
          setTelemetry(prev => ({ ...prev, ...msg.data }));
        } else if (msg.type === 'state') {
          setDetections(msg.data.active_detections || msg.data.detections || []);
          setStats(msg.data.summary || msg.data.stats || {});
          setMissionPhase(msg.data.mission_phase || 'SURVEY');
        } else if (msg.type === 'zones' || msg.type === 'ZONE_UPDATE') {
          setZones(msg.data || msg.zones || []);
        } else if (msg.type === 'NEW_DETECTION') {
          setDetections(prev => [msg.data, ...prev.filter(d => d.id !== msg.data.id)]);
        } else if (msg.type === 'NEW_DETECTIONS') {
          const incomingIds = new Set((msg.detections || []).map(d => d.id));
          setDetections(prev => [...(msg.detections || []), ...prev.filter(d => !incomingIds.has(d.id))]);
        }
      } catch (err) {
        console.error('WS message parse error', err);
      }
    };
  };

  const handleControlCommand = async (command, payload = {}) => {
    try {
      await fetch(`http://localhost:8000/api/mission/${command}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } catch (err) {
      console.error('Command failed', err);
    }
  };

  const handleSetFlightMode = async (mode) => {
    try {
      await fetch(`http://localhost:8000/api/drone/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      setTelemetry(prev => ({ ...prev, flight_mode: mode }));
    } catch (err) {
      console.error('Flight mode switch failed', err);
    }
  };

  const handleManualCommand = async (cmd) => {
    try {
      await fetch(`http://localhost:8000/api/drone/manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cmd)
      });
    } catch (err) {
      console.error('Manual command failed', err);
    }
  };

  const handleClearTrail = async () => {
    try {
      await fetch(`http://localhost:8000/api/drone/clear_trail`, { method: 'POST' });
      setTelemetry(prev => ({ ...prev, traversed_path: [] }));
    } catch (err) {
      console.error('Clear trail failed', err);
    }
  };

  const handleRTL = async () => {
    try {
      await fetch(`http://localhost:8000/api/drone/rtl`, { method: 'POST' });
    } catch (err) {
      console.error('RTL failed', err);
    }
  };

  const setPhase = async (phase) => {
    try {
      await fetch(`http://localhost:8000/api/mission/phase`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phase })
      });
      setMissionPhase(phase);
    } catch (err) {
      console.error(err);
    }
  };

  const [feedTimestamp, setFeedTimestamp] = useState(Date.now());
  const [streamMode, setStreamMode] = useState('direct');

  const setCamera = async (source) => {
    try {
      if (source === 'none') {
        await fetch(`http://localhost:8000/api/stream/stop`, { method: 'POST' });
        setTelemetry(prev => ({ ...prev, camera_active: false, camera_source: 'none' }));
      } else {
        const res = await fetch(`http://localhost:8000/api/stream/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source })
        });
        if (res.ok) {
          setFeedTimestamp(Date.now());
          setTelemetry(prev => ({ ...prev, camera_active: true, camera_source: source }));
        } else {
          const errData = await res.json().catch(() => ({}));
          alert(errData.detail || 'Failed to open camera source. Please check that IP Webcam is active and accessible.');
        }
      }
    } catch (err) {
      console.error('Camera stream error:', err);
    }
  };

  const locationTitle = telemetry?.mission_location?.name || "Riverside Village";

  return (
    <div className="app">
      {/* Topbar */}
      <div className="topbar">
        <div className="brand">
          <div className="brand-mark"></div>
          <div className="brand-text">
            <h1>RescueVision AI</h1>
            <p>{locationTitle} · eVTOL Autonomous Command Center</p>
          </div>
        </div>
        <div className="topbar-right">
          <div className="badge live" id="connBadge">
            <span className="dot"></span>
            <span>Command Link: {wsConnected ? 'Connected' : 'Offline'}</span>
          </div>
          <div className="clock">{new Date().toLocaleTimeString('en-IN', {hour12:false})} IST</div>
        </div>
      </div>

      {/* Mission Controls */}
      <MissionControls 
        telemetry={telemetry} 
        onCommand={handleControlCommand} 
        missionPhase={missionPhase} 
        setPhase={setPhase} 
        setCamera={setCamera}
        onSetFlightMode={handleSetFlightMode}
        onRTL={handleRTL}
        onClearTrail={handleClearTrail}
      />

      {/* Main Grid */}
      <div className="grid">
        <div className="col-left">
          {/* Map Panel */}
          <div className="panel">
            <div className="panel-head">
              <h2>Tactical map</h2>
              <span className="sub">
                {telemetry.flight_mode === 'MANUAL' ? '🕹️ MANUAL FLIGHT TRAIL OUTLINE' : '🤖 AUTOPILOT WAYPOINT NAVIGATION'}
              </span>
            </div>
            <div className="map-wrap">
              <DisasterMap 
                telemetry={telemetry} 
                detections={detections} 
                zones={zones} 
                missionPhase={missionPhase}
                onSelectDetection={setSelectedDetection}
                onManualCommand={handleManualCommand}
                onSetFlightMode={handleSetFlightMode}
                onClearTrail={handleClearTrail}
                onRTL={handleRTL}
              />
            </div>
          </div>

          {/* Camera Panel */}
          <div className="panel">
            <div className="panel-head">
              <h2>Aircraft view</h2>
              <div className="cam-toggle" style={{ display: 'flex', gap: '4px' }}>
                <button 
                  className={streamMode === 'direct' ? "active" : ""} 
                  onClick={() => setStreamMode('direct')}
                  title="Direct 0ms hardware stream from mobile camera"
                  style={streamMode === 'direct' ? { background: 'var(--teal)', color: '#0A0F14', fontWeight: 700 } : {}}
                >
                  ⚡ Direct (0-Lag)
                </button>
                <button 
                  className={streamMode === 'backend' ? "active" : ""} 
                  onClick={() => setStreamMode('backend')}
                  title="Backend AI pipeline processed stream"
                  style={streamMode === 'backend' ? { background: 'var(--teal)', color: '#0A0F14', fontWeight: 700 } : {}}
                >
                  🛰️ AI Backend
                </button>
                <button 
                  onClick={() => setFeedTimestamp(Date.now())}
                  title="Force re-sync video stream"
                  style={{ padding: '2px 8px', fontSize: '11px', color: 'var(--muted)' }}
                >
                  🔄
                </button>
              </div>
            </div>
            <div className="cam-wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', background: '#070b0e', minHeight: '260px' }}>
               {telemetry.camera_active ? (
                  <img 
                    key={`${streamMode}-${feedTimestamp}`}
                    src={
                      streamMode === 'direct' && telemetry.camera_source?.startsWith('http')
                        ? (telemetry.camera_source.endsWith('/video') || telemetry.camera_source.endsWith('.mjpeg') ? telemetry.camera_source : `${telemetry.camera_source.replace(/\/+$/, '')}/video`)
                        : `http://localhost:8000/video_feed?t=${feedTimestamp}`
                    }
                    alt="Drone Stream" 
                    style={{ width: '100%', height: '100%', maxHeight: '420px', objectFit: 'contain', display: 'block' }} 
                    onError={(e) => {
                      console.warn('Stream connection fallback to backend...');
                      if (streamMode === 'direct') {
                        setStreamMode('backend');
                      }
                    }}
                  />
               ) : (
                  <div style={{ color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: '12px', textAlign: 'center', padding: '20px' }}>
                    CAMERA OFF — Enter source path and click START FEED
                  </div>
               )}
               {telemetry.camera_active && (
                  <div className="cam-status" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span className="dot"></span>
                    <span>LIVE FEED · {streamMode === 'direct' && telemetry.camera_source?.startsWith('http') ? '⚡ 0ms Direct Mobile' : '🛰️ AI Engine'} ({telemetry.camera_source})</span>
                  </div>
               )}
            </div>
          </div>
        </div>

        <div className="col-right">
          <DetectionSummary stats={stats} telemetry={telemetry} zones={zones} />
          <AIInsights detections={detections} onSelect={setSelectedDetection} selectedDetection={selectedDetection} />
        </div>
      </div>
    </div>
  );
}
