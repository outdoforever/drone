import React, { useEffect, useState, useCallback } from 'react';

export default function ManualFlightHUD({ onManualCommand, flightMode, onSetFlightMode, onRTL, onClearTrail }) {
  const [speedMultiplier, setSpeedMultiplier] = useState(1.0);
  const [activeKey, setActiveKey] = useState(null);

  // Send directional vector
  const sendCommand = useCallback((vx, vy, vz = 0) => {
    if (onManualCommand) {
      onManualCommand({ vx, vy, vz, speed_scale: speedMultiplier });
    }
  }, [onManualCommand, speedMultiplier]);

  // Keyboard shortcut listener
  useEffect(() => {
    if (flightMode !== 'MANUAL') return;

    const baseSpeed = 8.0;

    const handleKeyDown = (e) => {
      // Don't trigger if typing in an input or textarea
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      const key = e.key.toLowerCase();
      setActiveKey(key);

      switch (key) {
        case 'w':
        case 'arrowup':
          sendCommand(0, baseSpeed, 0); // North
          break;
        case 's':
        case 'arrowdown':
          sendCommand(0, -baseSpeed, 0); // South
          break;
        case 'a':
        case 'arrowleft':
          sendCommand(-baseSpeed, 0, 0); // West
          break;
        case 'd':
        case 'arrowright':
          sendCommand(baseSpeed, 0, 0); // East
          break;
        case 'r': // Climb (VTOL Up)
          sendCommand(0, 0, 2.5);
          break;
        case 'f': // Descend (VTOL Down)
          sendCommand(0, 0, -2.5);
          break;
        case ' ': // Space = Hold / Hover
          e.preventDefault();
          sendCommand(0, 0, 0);
          break;
        default:
          break;
      }
    };

    const handleKeyUp = () => {
      setActiveKey(null);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [flightMode, sendCommand]);

  if (flightMode !== 'MANUAL') return null;

  return (
    <div style={{
      position: 'absolute',
      bottom: '48px',
      right: '12px',
      zIndex: 1000,
      background: 'rgba(8, 14, 20, 0.92)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(47, 217, 196, 0.4)',
      borderRadius: '10px',
      padding: '12px 14px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.65), 0 0 16px rgba(47, 217, 196, 0.15)',
      display: 'flex',
      flexDirection: 'column',
      gap: '10px',
      width: '210px',
      fontFamily: 'var(--mono, monospace)',
      userSelect: 'none'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '6px' }}>
        <span style={{ fontSize: '11px', fontWeight: 800, color: '#2FD9C4', letterSpacing: '0.5px' }}>
          🕹️ MANUAL PILOT HUD
        </span>
        <span style={{ fontSize: '9px', background: 'rgba(47, 217, 196, 0.15)', color: '#2FD9C4', padding: '2px 5px', borderRadius: '4px' }}>
          WASD LIVE
        </span>
      </div>

      {/* D-Pad Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '4px', justifyItems: 'center' }}>
        <div></div>
        <button
          onClick={() => sendCommand(0, 8.0, 0)}
          style={btnStyle(activeKey === 'w' || activeKey === 'arrowup')}
          title="Forward / North (W)"
        >
          ▲<br/><span style={{ fontSize: '8px' }}>W</span>
        </button>
        <div></div>

        <button
          onClick={() => sendCommand(-8.0, 0, 0)}
          style={btnStyle(activeKey === 'a' || activeKey === 'arrowleft')}
          title="Left / West (A)"
        >
          ◀ <span style={{ fontSize: '8px' }}>A</span>
        </button>

        <button
          onClick={() => sendCommand(0, 0, 0)}
          style={{ ...btnStyle(activeKey === ' '), background: 'rgba(255, 90, 82, 0.2)', borderColor: 'rgba(255, 90, 82, 0.5)', color: '#FF5A52' }}
          title="Hold / Hover (Space)"
        >
          🛑<br/><span style={{ fontSize: '7px' }}>HOLD</span>
        </button>

        <button
          onClick={() => sendCommand(8.0, 0, 0)}
          style={btnStyle(activeKey === 'd' || activeKey === 'arrowright')}
          title="Right / East (D)"
        >
          <span style={{ fontSize: '8px' }}>D</span> ▶
        </button>

        <div></div>
        <button
          onClick={() => sendCommand(0, -8.0, 0)}
          style={btnStyle(activeKey === 's' || activeKey === 'arrowdown')}
          title="Backward / South (S)"
        >
          <span style={{ fontSize: '8px' }}>S</span><br/>▼
        </button>
        <div></div>
      </div>

      {/* VTOL Vertical Altitude & Speed Controls */}
      <div style={{ display: 'flex', gap: '6px', justifyContent: 'space-between' }}>
        <button
          onClick={() => sendCommand(0, 0, 2.5)}
          style={{ ...btnStyle(activeKey === 'r'), flex: 1, padding: '5px 2px', fontSize: '10px' }}
          title="Climb (R)"
        >
          ⬆ CLIMB [R]
        </button>
        <button
          onClick={() => sendCommand(0, 0, -2.5)}
          style={{ ...btnStyle(activeKey === 'f'), flex: 1, padding: '5px 2px', fontSize: '10px' }}
          title="Descend (F)"
        >
          ⬇ DESCEND [F]
        </button>
      </div>

      {/* Speed Multiplier & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{ color: '#7C8B96' }}>SPEED:</span>
        <div style={{ display: 'flex', gap: '3px' }}>
          {[0.5, 1.0, 1.8].map(s => (
            <button
              key={s}
              onClick={() => setSpeedMultiplier(s)}
              style={{
                background: speedMultiplier === s ? '#2FD9C4' : 'rgba(255,255,255,0.06)',
                color: speedMultiplier === s ? '#0A0F14' : '#DCE6EC',
                border: 'none',
                borderRadius: '3px',
                padding: '2px 5px',
                fontSize: '9px',
                fontWeight: 700,
                cursor: 'pointer'
              }}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '4px' }}>
        <button
          onClick={onRTL}
          style={{
            flex: 1,
            background: 'rgba(255, 193, 7, 0.15)',
            border: '1px solid rgba(255, 193, 7, 0.4)',
            color: '#FFC107',
            borderRadius: '4px',
            padding: '4px',
            fontSize: '9px',
            fontWeight: 700,
            cursor: 'pointer'
          }}
        >
          🏠 RTL (HOME)
        </button>
        <button
          onClick={onClearTrail}
          style={{
            flex: 1,
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            color: '#7C8B96',
            borderRadius: '4px',
            padding: '4px',
            fontSize: '9px',
            cursor: 'pointer'
          }}
        >
          🧹 CLEAR TRAIL
        </button>
      </div>
    </div>
  );
}

function btnStyle(active) {
  return {
    background: active ? 'rgba(47, 217, 196, 0.45)' : 'rgba(47, 217, 196, 0.12)',
    border: `1px solid ${active ? '#2FD9C4' : 'rgba(47, 217, 196, 0.3)'}`,
    color: '#DCE6EC',
    borderRadius: '6px',
    width: '100%',
    padding: '6px 2px',
    fontSize: '11px',
    fontWeight: 700,
    cursor: 'pointer',
    textAlign: 'center',
    transition: 'all 0.1s ease',
    boxShadow: active ? '0 0 10px rgba(47, 217, 196, 0.5)' : 'none'
  };
}
