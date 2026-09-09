import React from 'react';
import { AlertCircle, Flame, Thermometer, MapPin, ChevronRight } from 'lucide-react';

export default function PriorityAlerts({ alerts, selectedId, onSelectAlert }) {
  return (
    <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h2 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-critical)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <AlertCircle size={18} color="var(--color-critical)" /> PRIORITY ALERTS
        </h2>
        <span className="mono-font" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          {alerts.length} URGENT
        </span>
      </div>

      {alerts.length === 0 ? (
        <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No critical or high priority alerts at this moment.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto', flex: 1, paddingRight: '4px' }}>
          {alerts.map((alert) => {
            const isSelected = selectedId === alert.id;
            const isCritical = alert.priority === 'CRITICAL';
            
            return (
              <div
                key={alert.id}
                onClick={() => onSelectAlert(alert)}
                style={{
                  background: isSelected ? 'rgba(0, 242, 254, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                  border: isSelected
                    ? '1px solid var(--accent-cyan)'
                    : isCritical
                    ? '1px solid rgba(255, 59, 48, 0.5)'
                    : '1px solid rgba(255, 149, 0, 0.4)',
                  borderRadius: '8px',
                  padding: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '0.65rem',
                      fontWeight: 800,
                      background: isCritical ? 'var(--color-critical)' : 'var(--color-high)',
                      color: '#FFF'
                    }}>
                      {alert.priority}
                    </span>
                    <span className="mono-font" style={{ fontWeight: 700, fontSize: '0.85rem', color: '#FFF' }}>
                      {alert.id}
                    </span>
                  </div>

                  <div className="mono-font" style={{ fontSize: '0.85rem', fontWeight: 800, color: isCritical ? 'var(--color-critical)' : 'var(--color-high)' }}>
                    RISK: {alert.risk_score}/100
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MapPin size={13} color="var(--accent-cyan)" /> Sector {alert.sector}
                  </span>
                  
                  {alert.thermal_confirmed && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-survivor)' }}>
                      <Thermometer size={13} /> Thermal YES
                    </span>
                  )}

                  {alert.nearby_fire && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-fire)' }}>
                      <Flame size={13} /> Fire Nearby
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  <span>Confidence: {(alert.confidence * 100).toFixed(0)}%</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '2px', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                    Focus Map <ChevronRight size={14} />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
