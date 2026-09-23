'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Header } from '../components/Header';
import { ControlPanel } from '../components/ControlPanel';
import { SystemStatusCard } from '../components/SystemStatusCard';
import { EmitterCard } from '../components/EmitterCard';
import { ReceiverCard } from '../components/ReceiverCard';
import { SpectrumVisualizer } from '../components/SpectrumVisualizer';
import { EventStream } from '../components/EventStream';

import { wsClient, ConnectionStatus } from '../lib/websocket';
import { api } from '../lib/api';
import {
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
  const [currentScan, setCurrentScan] = useState<ScanWindow | null>(null);
  const [lastObservation, setLastObservation] = useState<Observation | null>(null);
  const [lastEmittingId, setLastEmittingId] = useState<string | undefined>(undefined);
  const [events, setEvents] = useState<EventMessage[]>([]);

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

    const unsubEmitters = wsClient.subscribe('EMITTER_LIST', (payload) => {
      if (payload?.emitters) {
        setEmitters(payload.emitters);
      }
    });

    const unsubEmission = wsClient.subscribe('EMISSION_EVENT', (payload, timestamp) => {
      setLastEmittingId(payload.emitter_id);
      setTimeout(() => setLastEmittingId(undefined), 600);

      setEvents((prev) => [
        ...prev.slice(-150),
        { type: 'EMISSION_EVENT', timestamp, payload },
      ]);
    });

    const unsubScan = wsClient.subscribe('SCAN_REQUEST', (payload, timestamp) => {
      setCurrentScan(payload);
      setEvents((prev) => [
        ...prev.slice(-150),
        { type: 'SCAN_REQUEST', timestamp, payload },
      ]);
    });

    const unsubObs = wsClient.subscribe('RECEIVER_OBSERVATION', (payload, timestamp) => {
      setLastObservation(payload);
      if (payload?.scan) {
        setCurrentScan(payload.scan);
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
      unsubEmitters();
      unsubEmission();
      unsubScan();
      unsubObs();
      wsClient.disconnect();
    };
  }, [refreshData]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        connectionStatus={connectionStatus}
        simulationTime={systemStatus?.simulation_time || 0}
        simulationState={systemStatus?.simulation_state || 'PAUSED'}
        speed={systemStatus?.simulation_speed || 1.0}
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
          onRefreshStatus={refreshData}
        />

        {/* Spectrum Visualizer Canvas */}
        <SpectrumVisualizer
          emitters={emitters}
          currentScan={currentScan}
          lastObservation={lastObservation}
        />

        {/* Dual Grid: Receiver State & System Status */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '20px' }}>
          <ReceiverCard
            lastObservation={lastObservation}
            currentScan={currentScan}
            receiverStatus={systemStatus?.receiver_service || 'STOPPED'}
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
