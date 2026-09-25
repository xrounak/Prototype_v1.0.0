'use client';

import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw, FastForward, Scan, Radio, RefreshCw, Compass } from 'lucide-react';
import { api } from '../lib/api';

interface ControlPanelProps {
  simulationState: string;
  scannerStrategy?: string;
  onRefreshStatus?: () => void;
  onReset?: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  simulationState,
  scannerStrategy = 'round_robin',
  onRefreshStatus,
  onReset,
}) => {
  const [customStartFreqMhz, setCustomStartFreqMhz] = useState<number>(700);
  const [dwellMs, setDwellMs] = useState<number>(25);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [isStepping, setIsStepping] = useState<boolean>(false);
  const [autoSweep, setAutoSweep] = useState<boolean>(true);
  const [activeStrategy, setActiveStrategy] = useState<string>(scannerStrategy);
  const [isChangingStrategy, setIsChangingStrategy] = useState<boolean>(false);

  const isRunning = simulationState === 'RUNNING';

  useEffect(() => {
    if (scannerStrategy) {
      setActiveStrategy(scannerStrategy);
    }
  }, [scannerStrategy]);

  const handleTogglePlayPause = async () => {
    try {
      if (isRunning) {
        await api.pauseSimulation();
      } else {
        await api.startSimulation();
      }
      onRefreshStatus?.();
    } catch (err) {
      console.error('Failed to toggle play/pause:', err);
    }
  };

  const handleToggleAutoSweep = async () => {
    const nextVal = !autoSweep;
    setAutoSweep(nextVal);
    try {
      await api.setReceiverAutoScan(nextVal);
      onRefreshStatus?.();
    } catch (err) {
      console.error('Failed to toggle auto sweep:', err);
    }
  };

  const handleStrategyChange = async (newStrategy: string) => {
    try {
      setIsChangingStrategy(true);
      const res = await api.setReceiverScheduler(newStrategy);
      if (res?.strategy) {
        setActiveStrategy(res.strategy);
      }
      onRefreshStatus?.();
    } catch (err) {
      console.error('Failed to set scanner strategy:', err);
    } finally {
      setIsChangingStrategy(false);
    }
  };

  const handleStep = async (deltaSeconds: number = 0.025) => {
    try {
      setIsStepping(true);
      await api.stepSimulation(deltaSeconds);
      onRefreshStatus?.();
    } catch (err) {
      console.error('Failed to step simulation:', err);
    } finally {
      setIsStepping(false);
    }
  };

  const handleReset = async () => {
    try {
      await api.resetSimulation();
      onReset?.();
      onRefreshStatus?.();
    } catch (err) {
      console.error('Failed to reset simulation:', err);
    }
  };

  const handleExecuteScan = async (startFreqMhz: number, dwellTimeMs: number) => {
    try {
      setIsScanning(true);
      await api.executeScan({
        action_id: Math.floor(1000 + Math.random() * 9000),
        frequency_start_hz: startFreqMhz * 1_000_000,
        bandwidth_hz: 500_000_000, // 500 MHz instantaneous bandwidth
        dwell_time_ms: dwellTimeMs,
      });
      onRefreshStatus?.();
    } catch (err) {
      console.error('Failed to execute scan:', err);
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={16} color="#00f0ff" />
          SIMULATION &amp; RECEIVER SYNCHRONIZATION CONTROLS
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(2, 6, 23, 0.4)',
              border: `1px solid ${activeStrategy === 'random' ? 'rgba(168, 85, 247, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
              borderRadius: '6px',
              padding: '4px 10px',
              color: activeStrategy === 'random' ? '#c084fc' : '#38bdf8',
              fontWeight: 600,
            }}
            title="Active Receiver Scanner Strategy"
          >
            <Compass size={12} />
            SCANNER: {activeStrategy === 'random' ? 'RANDOM' : 'ROUND-ROBIN'}
          </div>

          <button
            onClick={handleToggleAutoSweep}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: autoSweep ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.2)',
              border: `1px solid ${autoSweep ? 'rgba(16, 185, 129, 0.4)' : 'rgba(100, 116, 139, 0.4)'}`,
              color: autoSweep ? '#34d399' : '#94a3b8',
              borderRadius: '6px',
              padding: '4px 10px',
              cursor: 'pointer',
              fontWeight: 600,
            }}
            title="Automatically sweep spectrum in sync with simulation clock"
          >
            <RefreshCw size={12} className={isRunning && autoSweep ? 'animate-spin' : ''} />
            Auto Receiver Sweep: {autoSweep ? 'SYNCED' : 'PAUSED'}
          </button>
          <span style={{ color: 'var(--text-muted)' }}>
            BW: 500 MHz
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '18px' }}>
        {/* Sim Engine Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
            Simulation Clock Controls
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
            <button
              onClick={handleTogglePlayPause}
              className={`btn ${isRunning ? 'btn-danger' : 'btn-emerald'}`}
              style={{ minWidth: '115px' }}
            >
              {isRunning ? <Pause size={16} /> : <Play size={16} />}
              {isRunning ? 'Pause Sim' : 'Run Sim'}
            </button>

            <button
              onClick={() => handleStep(0.025)}
              disabled={isStepping || isRunning}
              className="btn btn-primary"
              style={{ opacity: isRunning ? 0.5 : 1 }}
              title="Advance discrete 25ms simulation step with synchronized receiver dwell"
            >
              <FastForward size={16} />
              Step +25ms
            </button>

            <button
              onClick={handleReset}
              className="btn btn-secondary"
              title="Reset simulation time to 0.000s"
            >
              <RotateCcw size={16} />
              Reset
            </button>
          </div>
        </div>

        {/* Scanner Strategy Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
            Scanner Strategy
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <select
              value={activeStrategy}
              onChange={(e) => handleStrategyChange(e.target.value)}
              disabled={isChangingStrategy}
              aria-label="Scanner Strategy Selector"
              style={{
                background: 'rgba(30, 41, 59, 0.8)',
                border: '1px solid rgba(0, 240, 255, 0.4)',
                color: '#f1f5f9',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8rem',
                fontWeight: 600,
                borderRadius: '6px',
                padding: '6px 12px',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="round_robin">Round-Robin</option>
              <option value="random">Random</option>
            </select>
            <span
              style={{
                fontSize: '0.7rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                padding: '4px 8px',
                borderRadius: '4px',
                background: activeStrategy === 'random' ? 'rgba(168, 85, 247, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                color: activeStrategy === 'random' ? '#c084fc' : '#38bdf8',
                border: `1px solid ${activeStrategy === 'random' ? 'rgba(168, 85, 247, 0.3)' : 'rgba(56, 189, 248, 0.3)'}`,
                textTransform: 'uppercase',
              }}
            >
              {activeStrategy === 'random' ? 'Random Mode' : 'Sequential'}
            </span>
          </div>
        </div>


        {/* Custom Tune / Dwell Scan */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
            Manual Frequency Tuning
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '6px', padding: '4px 8px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '6px' }}>Freq:</span>
              <input
                type="number"
                value={customStartFreqMhz}
                onChange={(e) => setCustomStartFreqMhz(Number(e.target.value))}
                style={{ width: '65px', background: 'transparent', border: 'none', color: '#fff', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', outline: 'none' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>MHz</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(30, 41, 59, 0.6)', borderRadius: '6px', padding: '4px 8px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginRight: '6px' }}>Dwell:</span>
              <input
                type="number"
                value={dwellMs}
                onChange={(e) => setDwellMs(Number(e.target.value))}
                style={{ width: '45px', background: 'transparent', border: 'none', color: '#fff', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', outline: 'none' }}
              />
              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>ms</span>
            </div>

            <button
              onClick={() => handleExecuteScan(customStartFreqMhz, dwellMs)}
              disabled={isScanning}
              className="btn btn-primary"
              style={{ padding: '6px 12px' }}
            >
              <Scan size={14} />
              Tune
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
