'use client';

import React from 'react';
import { Server, Activity, Radio, Cpu, Power, Layers } from 'lucide-react';
import { SystemStatus } from '../lib/types';
import { api } from '../lib/api';

interface SystemStatusCardProps {
  status: SystemStatus | null;
  onRefresh?: () => void;
}

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({ status, onRefresh }) => {
  const handleToggleEmitter = async () => {
    try {
      if (status?.emitter_service === 'RUNNING') {
        await api.stopEmitter();
      } else {
        await api.startEmitter();
      }
      onRefresh?.();
    } catch (err) {
      console.error(err);
    }
  };

  const handleToggleReceiver = async () => {
    try {
      if (status?.receiver_service === 'RUNNING') {
        await api.stopReceiver();
      } else {
        await api.startReceiver();
      }
      onRefresh?.();
    } catch (err) {
      console.error(err);
    }
  };

  const items = [
    {
      title: 'Python Gateway',
      state: status?.gateway || 'DISCONNECTED',
      isRunning: status?.gateway === 'CONNECTED',
      icon: <Server size={18} color="#38bdf8" />,
      sub: 'FastAPI / WebSocket Bus',
    },
    {
      title: 'Active Environment',
      state: status?.environment_name || 'Open Sparse',
      isRunning: true,
      icon: <Layers size={18} color="#00f0ff" />,
      sub: `${status?.active_emitters ?? 0} of ${status?.total_emitters ?? 0} active`,
    },
    {
      title: 'Emitter Service',
      state: status?.emitter_service || 'STOPPED',
      isRunning: status?.emitter_service === 'RUNNING',
      icon: <Radio size={18} color="#a855f7" />,
      sub: `${status?.active_emitters ?? 0} active sources`,
      action: handleToggleEmitter,
    },
    {
      title: 'Receiver Service',
      state: status?.receiver_service || 'STOPPED',
      isRunning: status?.receiver_service === 'RUNNING',
      icon: <Cpu size={18} color="#10b981" />,
      sub: '500 MHz instantaneous BW',
      action: handleToggleReceiver,
    },
  ];

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
          <Activity size={15} color="#38bdf8" />
          SYSTEM STATUS &amp; SERVICES
        </h3>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
          Simulation State: <strong style={{ color: status?.simulation_state === 'RUNNING' ? '#34d399' : '#f59e0b' }}>{status?.simulation_state || 'PAUSED'}</strong>
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
        {items.map((item, idx) => (
          <div
            key={idx}
            style={{
              background: 'rgba(2, 6, 23, 0.4)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '12px 14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {item.icon}
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f1f5f9' }}>{item.title}</span>
              </div>
              <span
                style={{
                  fontSize: '0.7rem',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: item.isRunning ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: item.isRunning ? '#34d399' : '#f87171',
                  border: `1px solid ${item.isRunning ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                }}
              >
                {item.state}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '4px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{item.sub}</span>
              {item.action && (
                <button
                  onClick={item.action}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: item.isRunning ? '#f87171' : '#34d399',
                    fontSize: '0.7rem',
                    fontFamily: 'var(--font-mono)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                  title={`Toggle ${item.title}`}
                >
                  <Power size={11} />
                  {item.isRunning ? 'Stop' : 'Start'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
