import React, { useState, useEffect } from 'react';

export default function MissionControls({
  telemetry,
  onCommand,
  missionPhase,
  setPhase,
  setCamera,
  onSetFlightMode,
  onRTL,
  onClearTrail
}) {
  const { ai_active, drone_active, camera_source, flight_mode } = telemetry || {};
  const [sourceInput, setSourceInput] = useState(camera_source === 'none' ? '' : (camera_source || ''));

  useEffect(() => {
    if (camera_source && camera_source !== 'none') {
      setSourceInput(camera_source);
    }
  }, [camera_source]);

  const isSurvey = missionPhase === 'SURVEY';
  const isManual = flight_mode === 'MANUAL';

  const handleStartCamera = () => {
    if (sourceInput.trim()) setCamera(sourceInput.trim());
  };

  const handleStopCamera = () => {
    setSourceInput('');
    setCamera('none');
  };

  return (
    <div className="mission-control">
      {/* Flight Mode Toggle */}
      <div className="mc-field" style={{ minWidth: '170px' }}>
        <label>eVTOL FLIGHT MODE</label>
        <div className="cam-toggle">
          <button 
            className={!isManual ? "active" : ""} 
            onClick={() => onSetFlightMode && onSetFlightMode('AUTOPILOT')}
            style={!isManual ? { background: 'var(--teal)', color: '#0A0F14', fontWeight: 800 } : {}}
          >
            🤖 AUTOPILOT
          </button>
          <button 
            className={isManual ? "active" : ""} 
            onClick={() => onSetFlightMode && onSetFlightMode('MANUAL')}
            style={isManual ? { background: '#FFC107', color: '#0A0F14', fontWeight: 800 } : {}}
          >
            🕹️ MANUAL
          </button>
        </div>
      </div>

      {/* Mission Phase */}
      <div className="mc-field" style={{ minWidth: '150px' }}>
        <label>PHASE</label>
        <div className="cam-toggle">
          <button 
            className={isSurvey ? "active" : ""} 
            onClick={() => setPhase('SURVEY')}
          >
            SURVEY
          </button>
          <button 
            className={!isSurvey ? "active" : ""} 
            onClick={() => setPhase('SAR')}
          >
            SAR
          </button>
        </div>
      </div>

      {/* Camera Stream */}
      <div className="mc-field" style={{ flex: 1, minWidth: '180px' }}>
        <label>CAMERA SOURCE</label>
        <input 
          value={sourceInput} 
          onChange={e => setSourceInput(e.target.value)} 
          placeholder="Video path or webcam" 
        />
      </div>

      <div className="mc-actions">
        {camera_source === 'none' ? (
          <button className="btn btn-primary" onClick={handleStartCamera}>START FEED</button>
        ) : (
          <button className="btn btn-danger" onClick={handleStopCamera}>STOP FEED</button>
        )}
      </div>

      {/* AI Engine Status */}
      <div className="mc-field">
        <label>AI ENGINE</label>
        <div className={`status-pill ${ai_active ? 'active' : 'idle'}`}>
          {ai_active ? 'ACTIVE' : 'STANDBY'}
        </div>
      </div>

      {/* GPS Link Status */}
      <div className="mc-field">
        <label>GPS LINK</label>
        <div className={`status-pill ${telemetry?.gps_status?.includes('LIVE') ? 'active' : ''}`} style={telemetry?.gps_status?.includes('LIVE') ? { background: 'rgba(0,229,255,0.2)', color: '#00E5FF', borderColor: '#00E5FF' } : {}}>
          {telemetry?.gps_status === 'LIVE_MOBILE_GPS' ? '📱 LIVE MOBILE' : (telemetry?.gps_status || 'SIMULATED')}
        </div>
      </div>


      {/* Quick Mission Actions */}
      <div className="mc-actions" style={{ marginLeft: 'auto', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        <button
          className="btn"
          style={{ borderColor: 'rgba(255, 193, 7, 0.5)', color: '#FFC107' }}
          onClick={onRTL}
          title="Return to Launch / Base position"
        >
          🏠 RTL
        </button>
        <button
          className="btn"
          style={{ color: 'var(--muted)' }}
          onClick={onClearTrail}
          title="Clear traversed flight trail from map"
        >
          🧹 CLEAR TRAIL
        </button>
        <button className="btn btn-primary" onClick={() => onCommand('start')}>START MISSION</button>
        <button className="btn" onClick={() => onCommand('reset')}>RESET DATA</button>
        <button className="btn" style={{ color: 'var(--teal)', borderColor: 'var(--teal)' }} onClick={() => onCommand('inject_survivor')}>+ SURVIVOR</button>
        <button className="btn btn-danger" onClick={() => onCommand('inject_fire')}>+ FIRE</button>
      </div>
    </div>
  );
}
