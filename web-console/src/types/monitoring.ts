export interface RuntimeState {
  executionId: string;
  status: string;
  currentStep?: string;
  workerId?: string;
  heartbeatTime?: string;
}

export interface RuntimeStep {
  name: string;
  status: string;
}

export interface RuntimeExecutionState extends RuntimeState {
  steps?: RuntimeStep[];
}

export interface RuntimeTraceNode {
  id: string;
  type: string;
}

export interface RuntimeTraceState {
  nodes?: RuntimeTraceNode[];
}

export interface RuntimeHeartbeat {
  workerId: string;
  alive: boolean;
  lastSeen: string;
}
