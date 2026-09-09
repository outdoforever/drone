import React from 'react';
import { Play, Pause, RefreshCw, UserPlus, Flame, Filter } from 'lucide-react';

export default function SimulationControls({
  isRunning,
  onTogglePlay,
  onReset,
  onInjectSurvivor,
  onInjectFire,
  filterType,
  onSetFilter
}) {
  return (
    <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
      
      {/* Simulation Play / Pause / Reset controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button
          onClick={onTogglePlay}
          style={{
            background: isRunning ? 'rgba(255, 149, 0, 0.2)' : 'rgba(52, 199, 89, 0.2)',
            border: isRunning ? '1px solid var(--color-high)' : '1px solid var(--color-survivor)',
            color: isRunning ? 'var(--color-high)' : 'var(--color-survivor)',
            padding: '6px 14px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.78rem',
            fontWeight: 700
          }}
        >
          {isRunning ? <Pause size={14} /> : <Play size={14} />}
          {isRunning ? 'PAUSE SCAN' : 'START SCAN'}
        </button>

        <button
          onClick={onReset}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: 'var(--text-secondary)',
            padding: '6px 12px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.78rem'
          }}
        >
          <RefreshCw size={14} /> RESET DATA
        </button>
      </div>

      {/* Synthetic Injection triggers for testing */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>DEMO INJECT:</span>
        <button
          onClick={onInjectSurvivor}
          style={{
            background: 'rgba(0, 230, 118, 0.15)',
            border: '1px solid var(--color-survivor)',
            color: 'var(--color-survivor)',
            padding: '6px 10px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.72rem',
            fontWeight: 600
          }}
        >
          <UserPlus size={13} /> +SURVIVOR
        </button>

        <button
          onClick={onInjectFire}
          style={{
            background: 'rgba(255, 61, 0, 0.15)',
            border: '1px solid var(--color-fire)',
            color: 'var(--color-fire)',
            padding: '6px 10px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.72rem',
            fontWeight: 600
          }}
        >
          <Flame size={13} /> +FIRE HAZARD
        </button>
      </div>

      {/* Map Filter Toggles */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Filter size={14} color="var(--text-muted)" />
        <FilterBtn label="ALL" active={filterType === 'all'} onClick={() => onSetFilter('all')} />
        <FilterBtn label="SURVIVORS" active={filterType === 'person'} onClick={() => onSetFilter('person')} />
        <FilterBtn label="HAZARDS" active={filterType === 'hazards'} onClick={() => onSetFilter('hazards')} />
      </div>
    </div>
  );
}

function FilterBtn({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: active ? 'rgba(0, 242, 254, 0.2)' : 'transparent',
        border: active ? '1px solid var(--accent-cyan)' : '1px solid rgba(255, 255, 255, 0.08)',
        color: active ? 'var(--accent-cyan)' : 'var(--text-muted)',
        padding: '4px 10px',
        borderRadius: '4px',
        fontSize: '0.7rem',
        fontWeight: 600,
        cursor: 'pointer'
      }}
    >
      {label}
    </button>
  );
}
