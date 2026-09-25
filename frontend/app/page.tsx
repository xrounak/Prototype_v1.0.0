'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Header } from '../components/Header';
import { ControlPanel } from '../components/ControlPanel';
import { SystemStatusCard } from '../components/SystemStatusCard';
import { EmitterCard } from '../components/EmitterCard';
import { ReceiverCard } from '../components/ReceiverCard';
import { SpectrumTimeline } from '../components/spectrum/SpectrumTimeline';
import { EventStream } from '../components/EventStream';

import { wsClient, ConnectionStatus } from '../lib/websocket';
import { api } from '../lib/api';
import {
  EmissionEvent,
  EmitterConfig,
  EventMessage,
  Observation,
  ScanWindow,
  SystemStatus,
} from '../lib/types';

export default function Home() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('DISCONNECTED');
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [emitters, setEmitters] = useState<EmitterConfig[]>([]);
  const [emissionEvents, setEmissionEvents] = useState<EmissionEvent[]>([]);
  const [scanWindows, setScanWindows] = useState<ScanWindow[]>([]);
  const [currentScan, setCurrentScan] = useState<ScanWindow | null>(null);
  const [lastObservation, setLastObservation] = useState<Observation | null>(null);
  const [lastEmittingId, setLastEmittingId] = useState<string | undefined>(undefined);
  const [events, setEvents] = useState<EventMessage[]>([]);

  // Function to completely clear active timeline history on simulation reset or env change
  const clearAllHistory = useCallback(() => {
    setEmissionEvents([]);
    setScanWindows([]);
    setEvents([]);
    setCurrentScan(null);
    setLastObservation(null);
  }, []);

  // Refresh status & emitters from REST API
  const refreshData = useCallback(async () => {
    try {
      const [status, ems] = await Promise.all([
        api.getSystemStatus().catch(() => null),
        api.getEmitters().catch(() => []),
      ]);
      if (status) setSystemStatus(status);
      if (ems && ems.length > 0) setEmitters(ems);
    } catch (err) {
      console.error('Failed refreshing data:', err);
    }
  }, []);

  // Auto-detect clock rollback / restart to avoid ghost future events
  const prevSimTimeRef = useRef<number>(0);
  useEffect(() => {
    const curTime = systemStatus?.simulation_time ?? 0;
    if (curTime < prevSimTimeRef.current - 0.2) {
      clearAllHistory();
    }
    prevSimTimeRef.current = curTime;
  }, [systemStatus?.simulation_time, clearAllHistory]);

  // Connect WebSocket & subscribe to real-time events
  useEffect(() => {
    wsClient.connect();

    const unsubStatus = wsClient.onStatusChange((status) => {
      setConnectionStatus(status);
      if (status === 'CONNECTED') {
        refreshData();
      }
    });

    const unsubSystem = wsClient.subscribe('SYSTEM_STATUS', (payload) => {
      setSystemStatus(payload);
    });

    const unsubReset = wsClient.subscribe('SIMULATION_RESET', () => {
      clearAllHistory();
      refreshData();
    });

    const unsubEnvChanged = wsClient.subscribe('ENVIRONMENT_CHANGED', (payload) => {
      // Clear event buffer when switching environments so graph is clean
      clearAllHistory();
      refreshData();
    });

    const unsubEmitters = wsClient.subscribe('EMITTER_LIST', (payload) => {
      if (payload?.emitters) {
        setEmitters(payload.emitters);
      }
    });

    const unsubEmission = wsClient.subscribe('EMISSION_EVENT', (payload: EmissionEvent, timestamp: number) => {
      setLastEmittingId(payload.emitter_id);
      setTimeout(() => setLastEmittingId(undefined), 600);

      // Advance simulation clock with incoming real-time pulse timestamps
      setSystemStatus((prev) => {
        if (!prev) return null;
        if (timestamp > prev.simulation_time) {
          return { ...prev, simulation_time: timestamp };
        }
        return prev;
      });

      // Buffer emission events for 2D spectrum timeline (keep rich history up to 5,000 events / 60s)
      setEmissionEvents((prev) => {
        const cutoff = timestamp - 60;
        const filtered = prev.length > 5000 
          ? prev.filter((e) => e.time_end >= cutoff).slice(-4500)
          : prev;
        return [...filtered, payload];
      });

      setEvents((prev) => [
        ...prev.slice(-150),
        { type: 'EMISSION_EVENT', timestamp, payload },
      ]);
    });

    const unsubScan = wsClient.subscribe('SCAN_REQUEST', (payload: ScanWindow, timestamp: number) => {
      setCurrentScan(payload);
      setScanWindows((prev) => [...prev.slice(-300), payload]);
      setSystemStatus((prev) => (prev && timestamp > prev.simulation_time ? { ...prev, simulation_time: timestamp } : prev));

      setEvents((prev) => [
        ...prev.slice(-150),
        { type: 'SCAN_REQUEST', timestamp, payload },
      ]);
    });

    const unsubObs = wsClient.subscribe('RECEIVER_OBSERVATION', (payload: Observation, timestamp: number) => {
      setLastObservation(payload);
      if (payload?.scan) {
        setCurrentScan(payload.scan);
        setScanWindows((prev) => [...prev.slice(-300), payload.scan]);
      }
      setEvents((prev) => [
        ...prev.slice(-150),
        { type: 'RECEIVER_OBSERVATION', timestamp, payload },
      ]);
    });

    // Initial fetch
    refreshData();

    return () => {
      unsubStatus();
      unsubSystem();
      unsubReset();
      unsubEnvChanged();
      unsubEmitters();
      unsubEmission();
      unsubScan();
      unsubObs();
      wsClient.disconnect();
    };
  }, [refreshData, clearAllHistory]);

  const handleEnvironmentChange = async () => {
    clearAllHistory();
    await refreshData();
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        connectionStatus={connectionStatus}
        simulationTime={systemStatus?.simulation_time || 0}
        simulationState={systemStatus?.simulation_state || 'PAUSED'}
        speed={systemStatus?.simulation_speed || 1.0}
        environmentId={systemStatus?.environment_id || 'OPEN_SPARSE'}
        emitterCount={emitters.length || systemStatus?.total_emitters || 0}
        onEnvironmentChange={handleEnvironmentChange}
      />

      <div
        style={{
          maxWidth: '1440px',
          width: '100%',
          margin: '0 auto',
          padding: '24px 28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          flex: 1,
        }}
      >
        {/* Top Control Bar */}
        <ControlPanel
          simulationState={systemStatus?.simulation_state || 'PAUSED'}
          scannerStrategy={systemStatus?.scanner_strategy || 'round_robin'}
          onRefreshStatus={refreshData}
          onReset={clearAllHistory}
        />

        {/* Real-time Spectrum/Time Visualization (X = Frequency, Y = Simulation Time) */}
        <SpectrumTimeline
          simulationTime={systemStatus?.simulation_time || 0}
          simulationState={systemStatus?.simulation_state || 'PAUSED'}
          emitters={emitters}
          emissionEvents={emissionEvents}
          scanWindows={scanWindows}
          lastObservation={lastObservation}
        />

        {/* Dual Grid: Receiver State & System Status */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '20px' }}>
          <ReceiverCard
            lastObservation={lastObservation}
            currentScan={currentScan}
            receiverStatus={systemStatus?.receiver_service || 'STOPPED'}
            scannerStrategy={systemStatus?.scanner_strategy || 'round_robin'}
          />
          <SystemStatusCard
            status={systemStatus}
            onRefresh={refreshData}
          />
        </div>

        {/* Lower Grid: Emitter Environment & Live Event Stream */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '20px' }}>
          <EmitterCard
            emitters={emitters}
            lastEmittingId={lastEmittingId}
            onRefresh={refreshData}
          />
          <EventStream
            events={events}
            onClear={() => setEvents([])}
          />
        </div>
      </div>
    </div>
  );
}
