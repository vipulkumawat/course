// Application constants

export const CHAOS_SCENARIO_TYPES = {
  NETWORK_PARTITION: 'network_partition',
  RESOURCE_EXHAUSTION: 'resource_exhaustion',
  COMPONENT_FAILURE: 'component_failure',
  LATENCY_INJECTION: 'latency_injection',
  PACKET_LOSS: 'packet_loss'
};

export const SCENARIO_STATUS = {
  PENDING: 'pending',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  FAILED: 'failed',
  RECOVERED: 'recovered',
  TIMEOUT: 'timeout'
};

export const SEVERITY_LEVELS = {
  VERY_LOW: 1,
  LOW: 2,
  MEDIUM: 3,
  HIGH: 4,
  VERY_HIGH: 5
};

export const METRIC_THRESHOLDS = {
  CPU_WARNING: 70,
  CPU_CRITICAL: 90,
  MEMORY_WARNING: 80,
  MEMORY_CRITICAL: 95,
  DISK_WARNING: 85,
  DISK_CRITICAL: 95,
  LATENCY_WARNING: 100,
  LATENCY_CRITICAL: 500
};

export const REFRESH_INTERVALS = {
  METRICS: 5000,        // 5 seconds
  SCENARIOS: 10000,     // 10 seconds
  HEALTH_CHECK: 30000   // 30 seconds
};

export const API_ENDPOINTS = {
  HEALTH: '/health',
  SCENARIOS: '/api/chaos/scenarios',
  EMERGENCY_STOP: '/api/chaos/emergency-stop',
  METRICS: '/api/monitoring/metrics',
  METRICS_SUMMARY: '/api/monitoring/summary',
  CONFIG: '/api/config',
  SCENARIO_TEMPLATES: '/api/config/scenarios',
  RECOVERY_VALIDATE: '/api/recovery/validate'
};

export const WEBSOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  PERIODIC_UPDATE: 'periodic_update',
  SCENARIO_STARTED: 'scenario_started',
  SCENARIO_STOPPED: 'scenario_stopped',
  EMERGENCY_STOP: 'emergency_stop_completed',
  RECOVERY_VALIDATION: 'recovery_validation_completed',
  RECOVERY_FAILED: 'recovery_validation_failed'
};

export const DEFAULT_SCENARIO_DURATION = 300; // 5 minutes
export const DEFAULT_SEVERITY = 3;
export const MAX_BLAST_RADIUS = 0.3;
export const MAX_CONCURRENT_SCENARIOS = 3;
