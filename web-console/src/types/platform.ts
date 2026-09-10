export interface Agent {
  id: string;
  agent_code: string;
  agent_name: string;
  agent_type: string;
}

export interface ExecutionRecord {
  id: string;
  status: string;
  trace_id: string;
}

export interface WorkflowRun {
  id: string;
  status: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  memory_type?: string;
}

export interface TraceRecord {
  id: string;
  status: string;
}
