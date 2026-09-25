/**
 * REST API Client for Electronic Warfare Simulation Gateway.
 */
import {
  EmitterConfig,
  EnvironmentConfig,
  EnvironmentSummary,
  Observation,
  ScanRequest,
  SystemStatus,
} from './types';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

class ApiClient {
  private base: string;

  constructor(base: string = API_BASE) {
    this.base = base;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.base}${endpoint}`;
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...(options?.headers || {}),
        },
        ...options,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
      }

      return await response.json();
    } catch (err: any) {
      console.error(`Request to ${endpoint} failed:`, err);
      throw err;
    }
  }

  // Health
  async getHealth(): Promise<{ status: string; service: string }> {
    return this.request('/health');
  }

  // System Status
  async getSystemStatus(): Promise<SystemStatus> {
    return this.request('/api/system/status');
  }

  // Environments
  async getEnvironments(): Promise<EnvironmentSummary[]> {
    return this.request('/api/environments');
  }

  async getCurrentEnvironment(): Promise<EnvironmentConfig> {
    return this.request('/api/environment');
  }

  async selectEnvironment(environmentId: string): Promise<{ status: string; environment_id: string; environment_name: string; emitter_count: number }> {
    return this.request('/api/environment/select', {
      method: 'POST',
      body: JSON.stringify({ environment_id: environmentId }),
    });
  }

  // Simulation controls
  async startSimulation(speed: number = 1.0): Promise<{ status: string }> {
    return this.request('/api/simulation/start', {
      method: 'POST',
      body: JSON.stringify({ speed }),
    });
  }

  async pauseSimulation(): Promise<{ status: string }> {
    return this.request('/api/simulation/pause', { method: 'POST' });
  }

  async resetSimulation(): Promise<{ status: string }> {
    return this.request('/api/simulation/reset', { method: 'POST' });
  }

  async stepSimulation(deltaSeconds: number = 0.025): Promise<{ time_start: number; time_end: number; emissions_generated: number }> {
    return this.request('/api/simulation/step', {
      method: 'POST',
      body: JSON.stringify({ delta_seconds: deltaSeconds }),
    });
  }

  // Emitters
  async getEmitters(): Promise<EmitterConfig[]> {
    return this.request('/api/emitters');
  }

  async toggleEmitter(emitterId: string): Promise<{ emitter_id: string; active: boolean }> {
    return this.request(`/api/emitter/${emitterId}/toggle`, { method: 'POST' });
  }

  async startEmitter(): Promise<{ status: string }> {
    return this.request('/api/emitter/start', { method: 'POST' });
  }

  async stopEmitter(): Promise<{ status: string }> {
    return this.request('/api/emitter/stop', { method: 'POST' });
  }

  // Receiver
  async startReceiver(): Promise<{ status: string }> {
    return this.request('/api/receiver/start', { method: 'POST' });
  }

  async stopReceiver(): Promise<{ status: string }> {
    return this.request('/api/receiver/stop', { method: 'POST' });
  }

  async executeScan(scanRequest: ScanRequest): Promise<Observation> {
    return this.request('/api/receiver/scan', {
      method: 'POST',
      body: JSON.stringify(scanRequest),
    });
  }

  async setReceiverAutoScan(enabled: boolean): Promise<{ status: string; auto_scan: boolean }> {
    return this.request('/api/receiver/auto_scan', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  }

  // Scanner / Scheduler Strategy
  async getReceiverScheduler(): Promise<{ strategy: string; available_strategies: string[] }> {
    return this.request('/api/receiver/scheduler');
  }

  async setReceiverScheduler(strategy: string): Promise<{ status: string; strategy: string; available_strategies: string[] }> {
    return this.request('/api/receiver/scheduler', {
      method: 'POST',
      body: JSON.stringify({ strategy }),
    });
  }
}

export const api = new ApiClient();
