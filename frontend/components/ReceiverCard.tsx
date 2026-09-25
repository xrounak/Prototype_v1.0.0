'use client';

import React from 'react';
import { Cpu, Target, Clock, Radio, CheckCircle, Compass } from 'lucide-react';
import { Observation, ScanWindow } from '../lib/types';

interface ReceiverCardProps {
  lastObservation: Observation | null;
  currentScan: ScanWindow | null;
  receiverStatus: string;
  scannerStrategy?: string;
}

export const ReceiverCard: React.FC<ReceiverCardProps> = ({
  lastObservation,
  currentScan,
  receiverStatus,
  scannerStrategy,
}) => {
  const scan = currentScan || lastObservation?.scan;
  const activeStrategy = scannerStrategy || scan?.scheduler_strategy || 'round_robin';

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
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
          <Cpu size={16} color="#10b981" />
          RECEIVER STATE
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: activeStrategy === 'random' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(56, 189, 248, 0.15)',
              color: activeStrategy === 'random' ? '#c084fc' : '#38bdf8',
              border: `1px solid ${activeStrategy === 'random' ? 'rgba(168, 85, 247, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              textTransform: 'uppercase',
            }}
          >
            SCANNER: {activeStrategy.replace('_', '-')}
          </span>
          <span
            style={{
              fontSize: '0.7rem',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              background: receiverStatus === 'RUNNING' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: receiverStatus === 'RUNNING' ? '#34d399' : '#f87171',
              border: `1px solid ${receiverStatus === 'RUNNING' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            }}
          >
            {receiverStatus}
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '16px' }}>
        <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>CURRENT SCAN WINDOW</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#00f0ff', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
            {scan ? `${(scan.frequency_start_hz / 1e6).toFixed(0)} -> ${(scan.frequency_end_hz / 1e6).toFixed(0)} MHz` : '700 -> 1200 MHz'}
          </div>
        </div>

        <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>SCANNER STRATEGY</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: activeStrategy === 'random' ? '#c084fc' : '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: '4px', textTransform: 'uppercase' }}>
            {activeStrategy.replace('_', '-')}
          </div>
        </div>

        <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>INSTANTANEOUS BW</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
            500 MHz
          </div>
        </div>

        <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>DWELL DURATION</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
            {scan ? `${scan.dwell_time_ms} ms` : '25 ms'}
          </div>
        </div>

        <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>LAST DETECTIONS</div>
          <div style={{ fontSize: '1rem', fontWeight: 700, color: '#34d399', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
            {lastObservation ? `${lastObservation.detections.length} Signals` : '0 Signals'}
          </div>
        </div>
      </div>

      {/* Observation Breakdown */}
      {lastObservation && (
        <div style={{ background: 'rgba(2, 6, 23, 0.6)', borderRadius: '8px', padding: '12px 14px', border: '1px solid var(--border-active)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              Latest Observation: <strong style={{ color: '#fff' }}>{lastObservation.observation_id}</strong>
            </span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
              Timestamp: {lastObservation.timestamp.toFixed(3)}s
            </span>
          </div>

          {lastObservation.detections.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {lastObservation.detections.map((det) => (
                <div
                  key={det.detection_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    borderRadius: '6px',
                    padding: '6px 10px',
                    fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle size={14} color="#34d399" />
                    <span style={{ fontWeight: 700, color: '#34d399' }}>{det.emitter_id}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {(det.frequency_start_hz / 1e6).toFixed(1)} - {(det.frequency_end_hz / 1e6).toFixed(1)} MHz
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--text-muted)' }}>
                    <span>Pwr: {det.detected_power_dbm} dBm</span>
                    <span>Dur: {det.duration_us} &micro;s</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textAlign: 'center', padding: '8px 0' }}>
              No overlapping emissions detected in current dwell window.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
