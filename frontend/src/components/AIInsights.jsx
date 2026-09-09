import React from 'react';

export default function AIInsights({ detections, onSelect, selectedDetection }) {
  return (
    <div className="panel" style={{ flex: 1, minHeight: '300px' }}>
      <div className="panel-head">
        <h2>Field notes</h2>
        <span className="sub">{detections.length} events</span>
      </div>
      <div className="feed" style={{ overflowY: 'auto' }}>
        {detections.length === 0 ? (
          <div className="feed-empty">Nothing logged yet. Begin the sweep to watch the flight notes come in.</div>
        ) : (
          detections.map(det => {
            const isSurvivor = det.type === 'person';
            const icon = isSurvivor ? '⛑' : '⚠';
            const priorityClass = det.priority ? det.priority.toLowerCase() : 'medium';
            const isSelected = selectedDetection?.id === det.id;

            return (
              <div 
                key={det.id} 
                className="feed-item" 
                style={{ backgroundColor: isSelected ? 'var(--panel-2)' : 'transparent' }}
                onClick={() => onSelect(det)}
              >
                <div className={`feed-icon ${isSurvivor ? 'survivor' : 'hazard'}`}>{icon}</div>
                <div className="feed-main">
                  <div className="t1">
                    <span>{det.type.toUpperCase()}</span>
                    <span className={`pr-tag ${priorityClass}`}>{det.priority}</span>
                  </div>
                  <div className="t2">
                    {Math.round(det.confidence * 100)}% conf · Sector {det.sector || 'B4'} · {new Date(det.timestamp).toLocaleTimeString()}
                    {isSurvivor && det.health_status && ` · Health: ${det.health_status}`}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
