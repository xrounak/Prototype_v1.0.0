'use client';

import React, { useEffect, useState } from 'react';
import { Layers, ChevronDown, Check } from 'lucide-react';
import { api } from '../../lib/api';
import { EnvironmentSummary } from '../../lib/types';

interface EnvironmentSelectorProps {
  currentEnvironmentId?: string;
  emitterCount?: number;
  onEnvironmentChange?: (environmentId: string) => void;
}

export const EnvironmentSelector: React.FC<EnvironmentSelectorProps> = ({
  currentEnvironmentId = 'OPEN_SPARSE',
  emitterCount,
  onEnvironmentChange,
}) => {
  const [environments, setEnvironments] = useState<EnvironmentSummary[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(currentEnvironmentId);

  useEffect(() => {
    setSelectedId(currentEnvironmentId);
  }, [currentEnvironmentId]);

  useEffect(() => {
    let isMounted = true;
    const loadEnvironments = async () => {
      try {
        const envs = await api.getEnvironments();
        if (isMounted && envs && envs.length > 0) {
          setEnvironments(envs);
        }
      } catch (err) {
        console.error('Failed to load environments:', err);
      }
    };
    loadEnvironments();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSelect = async (envId: string) => {
    if (envId === selectedId) {
      setIsOpen(false);
      return;
    }

    try {
      setIsLoading(true);
      await api.selectEnvironment(envId);
      setSelectedId(envId);
      setIsOpen(false);
      onEnvironmentChange?.(envId);
    } catch (err) {
      console.error('Failed to switch environment:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const activeEnv = environments.find((e) => e.environment_id === selectedId) || {
    environment_id: selectedId,
    name: selectedId.replace('_', ' '),
    description: 'Electromagnetic simulation scenario',
    emitter_count: 0,
    spectrum: { min_frequency_hz: 300e6, max_frequency_hz: 18e9 },
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(15, 23, 42, 0.85)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: '8px',
          padding: '7px 14px',
          color: '#f8fafc',
          cursor: 'pointer',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          transition: 'all 0.2s ease',
          outline: 'none',
        }}
        title="Select simulation scenario / environment"
      >
        <Layers size={16} color="#00f0ff" />
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', textAlign: 'left' }}>
          <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Environment
          </span>
          <span style={{ fontWeight: 700, color: '#38bdf8' }}>
            {activeEnv.name}
          </span>
        </div>
        <span
          style={{
            fontSize: '0.65rem',
            background: 'rgba(56, 189, 248, 0.15)',
            color: '#7dd3fc',
            padding: '2px 6px',
            borderRadius: '4px',
            border: '1px solid rgba(56, 189, 248, 0.25)',
          }}
        >
          {emitterCount !== undefined ? emitterCount : activeEnv.emitter_count} Emitters
        </span>
        <ChevronDown size={14} color="#94a3b8" style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s ease' }} />
      </button>

      {isOpen && (
        <>
          <div
            onClick={() => setIsOpen(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 90 }}
          />
          <div
            style={{
              position: 'absolute',
              top: '100%',
              left: 0,
              marginTop: '6px',
              minWidth: '280px',
              background: 'rgba(10, 15, 26, 0.98)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: '8px',
              boxShadow: '0 12px 30px rgba(0, 0, 0, 0.7)',
              backdropFilter: 'blur(16px)',
              padding: '6px',
              zIndex: 100,
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            {environments.map((env) => {
              const isSelected = env.environment_id === selectedId;
              return (
                <button
                  key={env.environment_id}
                  onClick={() => handleSelect(env.environment_id)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    padding: '8px 10px',
                    borderRadius: '6px',
                    border: 'none',
                    background: isSelected ? 'rgba(14, 165, 233, 0.18)' : 'transparent',
                    cursor: 'pointer',
                    color: isSelected ? '#38bdf8' : '#e2e8f0',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                    width: '100%',
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                      {env.name}
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontSize: '0.65rem', color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>
                        {env.emitter_count} em
                      </span>
                      {isSelected && <Check size={14} color="#00f0ff" />}
                    </div>
                  </div>
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '2px', lineHeight: '1.2' }}>
                    {env.description}
                  </span>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
};
