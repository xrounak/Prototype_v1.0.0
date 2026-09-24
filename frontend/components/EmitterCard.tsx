'use client';

import React from 'react';
import { Radio, Zap, CheckCircle2, XCircle } from 'lucide-react';
import { EmitterConfig } from '../lib/types';
import { api } from '../lib/api';

interface EmitterCardProps {
  emitters: EmitterConfig[];
  lastEmittingId?: string;
  onRefresh?: () => void;
}

export const EmitterCard: React.FC<EmitterCardProps> = ({
  emitters,
  lastEmittingId,
  onRefresh,
}) => {
  const handleToggle = async (id: string) => {
    try {
      await api.toggleEmitter(id);
      onRefresh?.();
    } catch (err) {
      console.error(err);
    }
  };

  const getBehaviorBadge = (type: string = 'PERIODIC') => {
    switch (type) {
      case 'BURST':
        return { label: 'BURST', bg: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', border: 'rgba(6, 182, 212, 0.35)' };
      case 'PERIODIC':
        return { label: 'PERIODIC', bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.35)' };
      case 'CONTINUOUS':
        return { label: 'CONTINUOUS', bg: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: 'rgba(168, 85, 247, 0.35)' };
      case 'JITTERED':
        return { label: 'JITTERED', bg: 'rgba(234, 179, 8, 0.15)', color: '#fde047', border: 'rgba(234, 179, 8, 0.35)' };
      case 'STAGGERED':
        return { label: 'STAGGERED', bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.35)' };
      case 'FREQUENCY_HOPPING':
        return { label: 'FREQ HOPPING', bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.35)' };
      case 'FREQUENCY_AGILE':
        return { label: 'FREQ AGILE', bg: 'rgba(244, 63, 94, 0.15)', color: '#fb7185', border: 'rgba(244, 63, 94, 0.35)' };
      default:
        return { label: type, bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: 'rgba(148, 163, 184, 0.3)' };
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <h3
          style={{
            fontSize: '0.85rem',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Radio size={16} color="#a855f7" />
          ACTIVE EMITTER POPULATION
        </h3>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          {emitters.length} Sources In Scenario
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '480px', overflowY: 'auto' }}>
        {emitters.map((emitter) => {
          const freqHz = emitter.rf?.center_frequency_hz ?? emitter.frequency_hz ?? 0;
          const bwHz = emitter.rf?.bandwidth_hz ?? emitter.bandwidth_hz ?? 0;
          const pwr = emitter.rf?.power_dbm ?? emitter.power_dbm ?? 0;
          const bType = emitter.behavior?.type ?? emitter.behavior_type ?? 'PERIODIC';
          const category = emitter.category || 'RADAR';
          const subtype = emitter.subtype || '';
          const platform = emitter.spatial?.platform_type;

          const badge = getBehaviorBadge(bType);
          const isFlashing = lastEmittingId === emitter.emitter_id;

          const freqDisplay =
            freqHz >= 1e9 ? `${(freqHz / 1e9).toFixed(2)} GHz` : `${(freqHz / 1e6).toFixed(0)} MHz`;

          return (
            <div
              key={emitter.emitter_id}
              style={{
                background: isFlashing ? 'rgba(56, 189, 248, 0.2)' : 'rgba(2, 6, 23, 0.4)',
                border: isFlashing ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                transition: 'all 0.25s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div
                  style={{
                    background: emitter.active ? 'rgba(16, 185, 129, 0.1)' : 'rgba(148, 163, 184, 0.1)',
                    padding: '8px',
                    borderRadius: '6px',
                    border: `1px solid ${emitter.active ? 'rgba(16, 185, 129, 0.3)' : 'rgba(148, 163, 184, 0.2)'}`,
                  }}
                >
                  <Zap size={16} color={emitter.active ? '#34d399' : '#64748b'} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.88rem', color: '#f8fafc' }}>
                      {emitter.emitter_id}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {emitter.name || 'RF Emitter'}
                    </span>
                    <span style={{ fontSize: '0.62rem', color: '#94a3b8', background: 'rgba(255,255,255,0.06)', padding: '1px 5px', borderRadius: '3px' }}>
                      {category} {subtype ? `(${subtype})` : ''}
                    </span>
                    {platform && (
                      <span style={{ fontSize: '0.62rem', color: '#38bdf8', background: 'rgba(56,189,248,0.1)', padding: '1px 5px', borderRadius: '3px' }}>
                        {platform}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    <span>Freq: <strong style={{ color: '#e2e8f0' }}>{freqDisplay}</strong></span>
                    <span>BW: <strong style={{ color: '#e2e8f0' }}>{(bwHz / 1e6).toFixed(0)} MHz</strong></span>
                    <span>Pwr: <strong style={{ color: '#f59e0b' }}>{pwr} dBm</strong></span>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '4px',
                    background: badge.bg,
                    color: badge.color,
                    border: `1px solid ${badge.border}`,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {badge.label}
                </span>

                <button
                  onClick={() => handleToggle(emitter.emitter_id)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    color: emitter.active ? '#34d399' : '#94a3b8',
                  }}
                  title="Toggle emitter active status"
                >
                  {emitter.active ? <CheckCircle2 size={16} color="#34d399" /> : <XCircle size={16} color="#94a3b8" />}
                  {emitter.active ? 'ACTIVE' : 'INACTIVE'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
