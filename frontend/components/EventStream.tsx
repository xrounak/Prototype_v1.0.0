'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Trash2, ArrowDown } from 'lucide-react';
import { EventMessage } from '../lib/types';

interface EventStreamProps {
  events: EventMessage[];
  onClear: () => void;
}

export const EventStream: React.FC<EventStreamProps> = ({ events, onClear }) => {
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events, autoScroll]);

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'EMISSION_EVENT':
        return { bg: 'rgba(0, 240, 255, 0.15)', color: '#00f0ff', border: 'rgba(0, 240, 255, 0.3)' };
      case 'SCAN_REQUEST':
        return { bg: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', border: 'rgba(56, 189, 248, 0.3)' };
      case 'RECEIVER_OBSERVATION':
        return { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.3)' };
      case 'SYSTEM_STATUS':
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: 'rgba(148, 163, 184, 0.3)' };
      default:
        return { bg: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: 'rgba(168, 85, 247, 0.3)' };
    }
  };

  const formatPayload = (event: EventMessage) => {
    const p = event.payload || {};
    if (event.type === 'EMISSION_EVENT') {
      return `Emitter ${p.emitter_id} produced ${p.behavior} pulse (${p.duration_us}us) at ${(p.frequency_start_hz / 1e6).toFixed(1)}-${(p.frequency_end_hz / 1e6).toFixed(1)} MHz`;
    }
    if (event.type === 'SCAN_REQUEST') {
      return `Tune window ${(p.frequency_start_hz / 1e6).toFixed(1)} -> ${(p.frequency_end_hz / 1e6).toFixed(1)} MHz (BW 500 MHz, dwell ${p.dwell_time_ms}ms)`;
    }
    if (event.type === 'RECEIVER_OBSERVATION') {
      const dets = p.detections || [];
      const detSummary = dets.length > 0
        ? `Signals: ${dets.map((d: any) => `${d.emitter_id} (${d.detected_power_dbm}dBm)`).join(', ')}`
        : '0 signals detected';
      return `Observation ${p.observation_id}: ${detSummary}`;
    }
    if (event.type === 'SYSTEM_STATUS') {
      return `Gateway: ${p.gateway} | Emitter: ${p.emitter_service} | Receiver: ${p.receiver_service} | Active: ${p.active_emitters}`;
    }
    return JSON.stringify(p);
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Terminal size={16} color="#38bdf8" />
          <h3
            style={{
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            REAL-TIME EVENT STREAM
          </h3>
          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
            ({events.length} events logged)
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '0.7rem' }}
            title="Toggle autoscroll"
          >
            <ArrowDown size={12} color={autoScroll ? '#34d399' : '#94a3b8'} />
            {autoScroll ? 'Autoscroll ON' : 'Autoscroll OFF'}
          </button>
          <button
            onClick={onClear}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '0.7rem' }}
            title="Clear event log"
          >
            <Trash2 size={12} />
            Clear
          </button>
        </div>
      </div>

      {/* Terminal log container */}
      <div
        ref={containerRef}
        style={{
          height: '240px',
          overflowY: 'auto',
          background: 'rgba(2, 6, 23, 0.75)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
        }}
      >
        {events.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '90px' }}>
            Awaiting simulation events over WebSocket (/ws)...
          </div>
        ) : (
          events.map((ev, index) => {
            const badge = getEventBadge(ev.type);
            return (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  padding: '4px 0',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
                }}
              >
                <span style={{ color: 'var(--text-muted)', minWidth: '65px' }}>
                  [{ev.timestamp.toFixed(3)}]
                </span>
                <span
                  style={{
                    padding: '1px 6px',
                    borderRadius: '3px',
                    background: badge.bg,
                    color: badge.color,
                    border: `1px solid ${badge.border}`,
                    fontWeight: 600,
                    minWidth: '155px',
                    textAlign: 'center',
                    fontSize: '0.7rem',
                  }}
                >
                  {ev.type}
                </span>
                <span style={{ color: '#e2e8f0', wordBreak: 'break-word', flex: 1 }}>
                  {formatPayload(ev)}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
