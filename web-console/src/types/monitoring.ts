export interface RuntimeState {
  executionId: string;
  status: string;
  currentStep?: string;
  workerId?: string;
  heartbeatTime?: string;
}

export interface RuntimeHeartbeat {
  workerId: string;
  alive: boolean;
  lastSeen: string;
}
