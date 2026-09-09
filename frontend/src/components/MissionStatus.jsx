import React from 'react';
import { Activity, Radio, Cpu, BatteryCharging, Navigation, ShieldCheck, Radar, Search, Camera } from 'lucide-react';

export default function MissionStatus({ telemetry, missionPhase }) {
  const {
    drone_active = true,
    ai_active = true,
    gps_status = 'SIMULATED',
    network_status = 'ONLINE',
    mission_status = 'SEARCHING',
    latitude = 11.0168,
    longitude = 76.9558,
    altitude_m = 45.0,
    speed_ms = 6.5,
    battery_pct = 94.0,
    sector = 'B4',
    camera_source = 'none',
    camera_active = false
  } = telemetry || {};

  const isSurvey = missionPhase === 'SURVEY';
  const phaseLabel = isSurvey ? 'AREA SURVEY' : 'SEARCH & RESCUE';
  const phaseIcon = isSurvey ? <Radar size={14} /> : <Search size={14} />;

  return (
    <header className="glass-panel" style={{ padding: '14px 20px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        
        {/* Branding & Mission Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(0, 242, 254, 0.4)'
          }}>
            <Navigation size={24} color="#070a12" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '0.5px', background: 'linear-gradient(90deg, #FFFFFF, #94A3B8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              DISASTER RESPONSE COMMAND CENTER
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
              Autonomous Edge-AI Intelligence Pipeline • Software 20% Prototype
            </p>
          </div>
        </div>

        {/* Live Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: isSurvey ? 'rgba(0, 242, 254, 0.15)' : 'rgba(255, 59, 48, 0.15)',
            border: isSurvey ? '1px solid var(--accent-cyan)' : '1px solid var(--color-critical)',
            padding: '5px 12px', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 800,
            color: isSurvey ? 'var(--accent-cyan)' : 'var(--color-critical)'
          }}>
            {phaseIcon} {phaseLabel}
          </div>
          <StatusBadge icon={<Radio size={14} />} label="DRONE" value={mission_status} status="active" />
          <StatusBadge icon={<Cpu size={14} />} label="AI" value={ai_active ? "ACTIVE" : "OFF"} status="active" />
          <StatusBadge icon={<Activity size={14} />} label="GPS" value={gps_status} status="info" />
          <StatusBadge icon={<Camera size={14} />} label="CAMERA" value={camera_active ? 'LIVE' : 'OFF'} status={camera_active ? 'active' : 'info'} />
          <StatusBadge icon={<ShieldCheck size={14} />} label="NET" value={network_status} status="active" />
        </div>
      </div>

      {/* Telemetry Data Bar */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '8px',
        background: 'rgba(0, 0, 0, 0.25)',
        padding: '8px 12px',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        fontSize: '0.78rem'
      }}>
        <TelemetryField label="SECTOR" value={sector} highlight />
        <TelemetryField label="LATITUDE" value={latitude.toFixed(4)} />
        <TelemetryField label="LONGITUDE" value={longitude.toFixed(4)} />
        <TelemetryField label="ALTITUDE" value={`${altitude_m.toFixed(1)} m`} />
        <TelemetryField label="SPEED" value={`${speed_ms.toFixed(1)} m/s`} />
        <TelemetryField label="BATTERY" value={`${battery_pct}%`} icon={<BatteryCharging size={13} color="var(--color-survivor)" />} />
      </div>
    </header>
  );
}

function StatusBadge({ icon, label, value, status }) {
  const isGreen = status === 'active';
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      background: 'rgba(255, 255, 255, 0.04)',
      padding: '6px 10px',
      borderRadius: '6px',
      border: '1px solid rgba(255, 255, 255, 0.08)',
      fontSize: '0.75rem'
    }}>
      <span style={{ color: isGreen ? 'var(--color-survivor)' : 'var(--accent-cyan)' }}>{icon}</span>
      <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>{label}:</span>
      <span style={{
        fontWeight: 700,
        color: isGreen ? 'var(--color-survivor)' : 'var(--accent-cyan)',
        fontFamily: 'var(--font-mono)'
      }}>
        🟢 {value}
      </span>
    </div>
  );
}

function TelemetryField({ label, value, highlight, icon }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      {icon}
      <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem', fontWeight: 600 }}>{label}:</span>
      <span style={{
        fontFamily: 'var(--font-mono)',
        fontWeight: 700,
        color: highlight ? 'var(--accent-cyan)' : 'var(--text-primary)'
      }}>
        {value}
      </span>
    </div>
  );
}
