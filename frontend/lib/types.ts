/**
 * Frontend TypeScript type definitions mirroring backend EW simulation models.
 */

export type BehaviorType =
  | 'CONTINUOUS'
  | 'PERIODIC'
  | 'BURST'
  | 'JITTERED'
  | 'STAGGERED'
  | 'FREQUENCY_HOPPING'
  | 'FREQUENCY_AGILE';

export interface RFProfile {
  center_frequency_hz: number;
  bandwidth_hz: number;
  power_dbm: number;
}

export interface SpatialProfile {
  x_m: number;
  y_m: number;
  z_m: number;
  platform_type: string;
}

export interface ModulationProfile {
  type: string;
  parameters?: Record<string, any>;
}

export interface BehaviorConfig {
  type: BehaviorType;
  pulse_width_us?: number;
  repetition_interval_ms?: number;
  burst_count?: number;
  burst_interval_ms?: number;
  base_pri_ms?: number;
  jitter_percent?: number;
  pri_sequence_ms?: number[];
  hop_frequencies_hz?: number[];
  dwell_time_ms?: number;
  min_frequency_hz?: number;
  max_frequency_hz?: number;
  change_interval_ms?: number;
}

export interface EmitterConfig {
  emitter_id: string;
  name?: string;
  category?: string;
  subtype?: string;
  rf?: RFProfile;
  spatial?: SpatialProfile;
  behavior?: BehaviorConfig;
  modulation?: ModulationProfile;
  active: boolean;

  // Convenience flat fields for backward compatibility
  frequency_hz?: number;
  bandwidth_hz?: number;
  power_dbm?: number;
  pulse_duration_us?: number;
  repetition_interval_ms?: number;
  burst_count?: number;
  behavior_type?: BehaviorType;
}

export interface EmissionEvent {
  type: string;
  event_id: string;
  emitter_id: string;
  timestamp: number;
  time_end: number;
  emitter_category?: string;
  emitter_subtype?: string;
  frequency_start_hz: number;
  frequency_end_hz: number;
  bandwidth_hz?: number;
  duration_us: number;
  power_dbm: number;
  behavior: string;
  modulation?: string;
  sequence_number?: number;
}

export interface ScanRequest {
  type?: string;
  action_id: number | string;
  frequency_start_hz: number;
  bandwidth_hz?: number;
  dwell_time_ms?: number;
  state_version?: number;
}

export interface ScanWindow {
  action_id?: number | string;
  frequency_start_hz: number;
  frequency_end_hz: number;
  dwell_time_ms: number;
  time_start: number;
  time_end: number;
  scheduler_strategy?: string;
}

export interface Detection {
  detection_id: string;
  emitter_id: string;
  emitter_category?: string;
  emitter_subtype?: string;
  frequency_start_hz: number;
  frequency_end_hz: number;
  detected_power_dbm: number;
  observed_power_dbm?: number;
  timestamp: number;
  duration_us: number;
  overlap_ratio: number;
  behaviour?: string;
  modulation?: string;
}

export interface Observation {
  type: string;
  observation_id: string;
  timestamp: number;
  scan: ScanWindow;
  detections: Detection[];
}

export interface SpectrumLimits {
  min_frequency_hz: number;
  max_frequency_hz: number;
}

export interface EnvironmentSummary {
  environment_id: string;
  name: string;
  description: string;
  emitter_count: number;
  spectrum: SpectrumLimits;
}

export interface EnvironmentConfig {
  environment_id: string;
  name: string;
  description: string;
  duration_seconds: number;
  spectrum: SpectrumLimits;
  emitter_count: number;
  emitters: EmitterConfig[];
}

export interface SystemStatus {
  gateway: string;
  emitter_service: string;
  receiver_service: string;
  simulation_time: number;
  simulation_state: 'RUNNING' | 'PAUSED' | 'STOPPED';
  simulation_speed: number;
  environment_id: string;
  environment_name: string;
  total_emitters: number;
  active_emitters: number;
  receiver_bandwidth_hz: number;
  last_observation_id?: string;
  scanner_strategy?: string;
}

export interface SchedulerStatus {
  strategy: string;
  available_strategies: string[];
}

export interface EventMessage {
  type: string;
  timestamp: number;
  payload: any;
}
