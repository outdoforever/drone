import React from 'react';

function getHeadingCardinal(deg) {
  const norm = ((deg % 360) + 360) % 360;
  if (norm >= 337.5 || norm < 22.5) return 'NORTH (N)';
  if (norm >= 22.5 && norm < 67.5) return 'NORTHEAST (NE)';
  if (norm >= 67.5 && norm < 112.5) return 'EAST (E)';
  if (norm >= 112.5 && norm < 157.5) return 'SOUTHEAST (SE)';
  if (norm >= 157.5 && norm < 202.5) return 'SOUTH (S)';
  if (norm >= 202.5 && norm < 247.5) return 'SOUTHWEST (SW)';
  if (norm >= 247.5 && norm < 292.5) return 'WEST (W)';
  return 'NORTHWEST (NW)';
}

export default function DetectionSummary({ stats, telemetry, zones = [] }) {

  const {
    survivors_total = 0,
    fire_count = 0,
    flood_count = 0,
    debris_count = 0,
    damaged_structures_count = 0,
    smoke_count = 0,
    zones_mapped = 0
  } = stats || {};

  const battery_pct = telemetry?.battery_pct || 100;
  const hazardsCount = fire_count + flood_count + debris_count + damaged_structures_count + smoke_count;
  const criticalAlerts = (stats?.survivors_critical || 0) + fire_count;

  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Flight notes</h2>
        <span className="sub">UPDATED LIVE</span>
      </div>
      <div className="panel-body">
        <div style={{ marginBottom: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted-2)' }}>Battery remaining</label>
            <div className="battery-row">
              <div className="battery-bar">
                <i style={{ width: `${battery_pct}%`, background: battery_pct < 25 ? 'var(--red)' : battery_pct < 50 ? 'var(--amber)' : 'var(--green)' }}></i>
              </div>
              <span style={{ fontFamily: 'var(--mono)', fontSize: '12px' }}>{Math.round(battery_pct)}%</span>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--muted-2)' }}>Camera Bearing / Pole</label>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(47,217,196,0.3)',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '11px',
              fontFamily: 'var(--mono, monospace)',
              color: '#2FD9C4',
              fontWeight: 700
            }}>
              <span>🧭</span>
              <span>{Math.round(telemetry?.heading_deg || 0)}°</span>
              <span style={{ color: '#FFD700', marginLeft: 'auto' }}>
                {getHeadingCardinal(telemetry?.heading_deg || 0)}
              </span>
            </div>
          </div>
        </div>

        
        <div className="stat-grid">
          <div className="stat ok">
            <div className="n">{survivors_total}</div>
            <div className="l">People verified</div>
          </div>
          <div className="stat alert">
            <div className="n">{hazardsCount}</div>
            <div className="l">Hazards marked</div>
          </div>
          <div className="stat">
            <div className="n">{zones.length || zones_mapped}</div>
            <div className="l">Disaster Zones</div>
          </div>
          <div className="stat alert">
            <div className="n">{criticalAlerts}</div>
            <div className="l">Needs attention</div>
          </div>
          <div className="stat">
            <div className="n">{stats?.total_detections || 0}</div>
            <div className="l">Total Objects</div>
          </div>
          <div className="stat ok">
            <div className="n">{(stats?.total_detections || 0) + (zones.length || 0)}</div>
            <div className="l">Notes logged</div>
          </div>
        </div>
      </div>
    </div>
  );
}
