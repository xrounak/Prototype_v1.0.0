'use client';

import React from 'react';
import { ConnectionStatus } from '../lib/websocket';
import { Radio, Clock } from 'lucide-react';
import { EnvironmentSelector } from './environment/EnvironmentSelector';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  simulationTime: number;
  simulationState: string;
  speed: number;
  environmentId?: string;
  emitterCount?: number;
  onEnvironmentChange?: (environmentId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  connectionStatus,
  simulationTime,
  simulationState,
  speed,
  environmentId = 'OPEN_SPARSE',
  emitterCount,
  onEnvironmentChange,
}) => {
  const statusColorClass =
    connectionStatus === 'CONNECTED'
      ? 'pulse-connected'
      : connectionStatus === 'CONNECTING'
      ? 'pulse-connecting'
      : 'pulse-disconnected';

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 28px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(8, 11, 18, 0.95)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        flexWrap: 'wrap',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(14,165,233,0.2), rgba(16,185,129,0.2))',
            padding: '10px',
            borderRadius: '10px',
            border: '1px solid var(--border-active)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Radio size={24} color="#00f0ff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#ffffff' }}>
              EW SIMULATION PLATFORM
            </h1>
            <span
              style={{
                fontSize: '0.65rem',
                fontFamily: 'var(--font-mono)',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                padding: '2px 8px',
                borderRadius: '4px',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                fontWeight: 600,
              }}
            >
              MULTI-ENVIRONMENT FOUNDATION
            </span>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Modular Emitters &bull; Behaviour Strategies &bull; 2D Spectrum Timeline &bull; 500 MHz Receiver
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        {/* Dynamic Environment Selector Dropdown */}
        <EnvironmentSelector
          currentEnvironmentId={environmentId}
          emitterCount={emitterCount}
          onEnvironmentChange={onEnvironmentChange}
        />

        {/* Simulation Clock Display */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '7px 14px',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <Clock size={16} color="#38bdf8" />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sim Clock
            </span>
            <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.04em' }}>
              {simulationTime.toFixed(3)}s
            </span>
          </div>
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 600,
              padding: '2px 6px',
              borderRadius: '4px',
              background: simulationState === 'RUNNING' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(148, 163, 184, 0.15)',
              color: simulationState === 'RUNNING' ? '#34d399' : '#94a3b8',
              marginLeft: '4px',
            }}
          >
            {simulationState}
          </span>
        </div>

        {/* Connection status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '8px',
            padding: '7px 12px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
          }}
        >
          <span className={`pulse-dot ${statusColorClass}`} />
          <span style={{ fontWeight: 600, color: '#f1f5f9' }}>
            {connectionStatus}
          </span>
        </div>
      </div>
    </header>
  );
};
