export interface RuntimeNode {
  id: string;
  name: string;
  type: 'agent' | 'skill' | 'tool' | 'artifact';
  status: string;
  startedTime?: string;
  finishedTime?: string;
}

export interface RuntimeTrace {
  traceId: string;
  nodes: RuntimeNode[];
}
