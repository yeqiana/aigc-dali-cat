export interface RuntimeStreamEvent {
  executionId: string;
  eventType: string;
  nodeId?: string;
  nodeName?: string;
  status?: string;
  timestamp: string;
}
