'use client';

import React, { useMemo } from 'react';
import { Radio, Eye } from 'lucide-react';
import { EmitterConfig, Observation, ScanWindow } from '../lib/types';

interface SpectrumVisualizerProps {
  emitters: EmitterConfig[];
  currentScan: ScanWindow | null;
  lastObservation: Observation | null;
}

export const SpectrumVisualizer: React.FC<SpectrumVisualizerProps> = ({
  emitters,
  currentScan,
  lastObservation,
}) => {
  const minFreqHz = 500_000_000;   // 500 MHz
  const maxFreqHz = 2_000_000_000; // 2000 MHz (2.0 GHz)
  const totalSpanHz = maxFreqHz - minFreqHz;

  // Convert Hz to percentage position along the spectrum axis
  const freqToPercent = (freqHz: number) => {
    const clamped = Math.max(minFreqHz, Math.min(maxFreqHz, freqHz));
    return ((clamped - minFreqHz) / totalSpanHz) * 100;
  };

  const activeScan = currentScan || lastObservation?.scan || {
    frequency_start_hz: 700_000_000,
    frequency_end_hz: 1_200_000_000,
    dwell_time_ms: 25,
    time_start: 0,
    time_end: 0,
  };

  const scanStartPct = freqToPercent(activeScan.frequency_start_hz);
  const scanEndPct = freqToPercent(activeScan.frequency_end_hz);
  const scanWidthPct = Math.max(1, scanEndPct - scanStartPct);

  // Ticks along the frequency axis
  const ticks = [500, 750, 1000, 1250, 1500, 1750, 2000];

  const detectedEmitterIds = useMemo(() => {
    if (!lastObservation) return new Set<string>();
    return new Set(lastObservation.detections.map((d) => d.emitter_id));
  }, [lastObservation]);

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
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
          <Eye size={16} color="#00f0ff" />
          ELECTROMAGNETIC SPECTRUM &amp; SCAN WINDOW
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(56, 189, 248, 0.3)', border: '1px solid #38bdf8', borderRadius: '2px' }} />
            Receiver Scan (500 MHz)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(0, 240, 255, 0.6)', borderRadius: '2px' }} />
            Burst Emitter
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(245, 158, 11, 0.6)', borderRadius: '2px' }} />
            Periodic Emitter
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '10px', height: '10px', background: 'rgba(168, 85, 247, 0.6)', borderRadius: '2px' }} />
            Continuous Emitter
          </span>
        </div>
      </div>

      {/* Main Spectrum Visualizer Display */}
      <div
        style={{
          position: 'relative',
          height: '140px',
          background: 'radial-gradient(ellipse at bottom, rgba(14, 165, 233, 0.05) 0%, rgba(2, 6, 23, 0.95) 100%)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          overflow: 'hidden',
          marginBottom: '10px',
        }}
      >
        {/* Grid lines */}
        {ticks.map((t) => {
          const leftPct = freqToPercent(t * 1_000_000);
          return (
            <div
              key={t}
              style={{
                position: 'absolute',
                left: `${leftPct}%`,
                top: 0,
                bottom: 0,
                width: '1px',
                background: 'rgba(255, 255, 255, 0.04)',
                borderRight: '1px dashed rgba(56, 189, 248, 0.1)',
              }}
            />
          );
        })}

        {/* Noise floor baseline wave */}
        <div
          style={{
            position: 'absolute',
            bottom: '15px',
            left: 0,
            right: 0,
            height: '2px',
            background: 'rgba(56, 189, 248, 0.25)',
            boxShadow: '0 0 8px rgba(56, 189, 248, 0.3)',
          }}
        />

        {/* Receiver Scan Window Bracket (500 MHz) */}
        <div
          style={{
            position: 'absolute',
            left: `${scanStartPct}%`,
            width: `${scanWidthPct}%`,
            top: 0,
            bottom: 0,
            background: 'linear-gradient(180deg, rgba(14, 165, 233, 0.18) 0%, rgba(14, 165, 233, 0.02) 100%)',
            borderLeft: '2px solid #00f0ff',
            borderRight: '2px solid #00f0ff',
            boxShadow: 'inset 0 0 20px rgba(0, 240, 255, 0.1)',
            pointerEvents: 'none',
            zIndex: 10,
            transition: 'left 0.4s ease, width 0.4s ease',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '6px',
              left: '50%',
              transform: 'translateX(-50%)',
              background: 'rgba(8, 11, 18, 0.85)',
              padding: '2px 8px',
              borderRadius: '4px',
              border: '1px solid rgba(0, 240, 255, 0.4)',
              fontSize: '0.65rem',
              fontFamily: 'var(--font-mono)',
              color: '#00f0ff',
              whiteSpace: 'nowrap',
            }}
          >
            RX WINDOW [500 MHz]
          </div>
        </div>

        {/* Emitters Placed on Spectrum */}
        {emitters.map((em) => {
          const bw = em.rf?.bandwidth_hz ?? em.bandwidth_hz ?? 20_000_000;
          const freq = em.rf?.center_frequency_hz ?? em.frequency_hz ?? 1_000_000_000;
          const pwr = em.rf?.power_dbm ?? em.power_dbm ?? 30;
          const bType = em.behavior?.type ?? em.behavior_type ?? 'BURST';

          const halfBw = bw / 2.0;
          const leftPct = freqToPercent(freq - halfBw);
          const rightPct = freqToPercent(freq + halfBw);
          const widthPct = Math.max(1.5, rightPct - leftPct);
          const isDetected = detectedEmitterIds.has(em.emitter_id);

          const color =
            bType === 'BURST'
              ? '#00f0ff'
              : bType === 'PERIODIC'
              ? '#f59e0b'
              : '#c084fc';

          return (
            <div
              key={em.emitter_id}
              style={{
                position: 'absolute',
                left: `${leftPct}%`,
                width: `${widthPct}%`,
                bottom: '15px',
                height: `${Math.min(95, Math.max(35, (pwr + 10) * 1.8))}px`,
                background: em.active
                  ? `linear-gradient(180deg, ${color} 0%, rgba(15, 23, 42, 0.4) 100%)`
                  : 'rgba(100, 116, 139, 0.3)',
                borderRadius: '4px 4px 0 0',
                border: `1px solid ${em.active ? color : 'rgba(100, 116, 139, 0.5)'}`,
                boxShadow: isDetected && em.active ? `0 0 16px ${color}` : 'none',
                zIndex: 20,
                transition: 'all 0.3s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-start',
                paddingTop: '4px',
              }}
            >
              <span
                style={{
                  fontSize: '0.65rem',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  color: em.active ? '#ffffff' : '#94a3b8',
                  textShadow: '0 0 4px #000',
                }}
              >
                {em.emitter_id}
              </span>
              {isDetected && em.active && (
                <span
                  style={{
                    fontSize: '0.55rem',
                    fontFamily: 'var(--font-mono)',
                    color: '#34d399',
                    background: 'rgba(0,0,0,0.7)',
                    padding: '1px 3px',
                    borderRadius: '2px',
                    marginTop: '2px',
                  }}
                >
                  HIT
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Frequency Axis Markings */}
      <div style={{ position: 'relative', height: '24px', margin: '0 4px' }}>
        {ticks.map((t) => {
          const leftPct = freqToPercent(t * 1_000_000);
          return (
            <div
              key={t}
              style={{
                position: 'absolute',
                left: `${leftPct}%`,
                transform: 'translateX(-50%)',
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
              }}
            >
              {t} MHz
            </div>
          );
        })}
      </div>
    </div>
  );
};
