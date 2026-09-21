export interface Agent {
  id: string;
  agent_code: string;
  agent_name: string;
  agent_type: string;
  description?: string;
  status?: string;
}

export interface SkillExecutionRecord {
  skill_execution_id: string;
  skill_code: string;
  skill_version: string;
  status: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error: string | null;
  started_time: string;
  finished_time: string | null;
}

export interface ToolExecutionRecord {
  tool_execution_id: string;
  skill_execution_id: string;
  tool_code: string;
  status: string;
  request_data: Record<string, unknown>;
  response_data: Record<string, unknown>;
  error: string | null;
  started_time: string;
  finished_time: string | null;
}

export interface ExecutionRecord {
  execution_id: string;
  agent_code: string;
  agent_version: string;
  execution_type: string;
  status: string;
  input_context: Record<string, unknown>;
  output_result: Record<string, unknown>;
  error: string | null;
  trace_id: string;
  skill_executions: SkillExecutionRecord[];
  tool_executions: ToolExecutionRecord[];
  started_time: string;
  finished_time: string | null;
  created_time: string;
  updated_time: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  memory_type?: string;
  evidence_ref?: string;
  outcome?: string;
  confidence?: number;
}

export interface TraceRecord {
  trace_id: string;
  span_id: string;
  operation: string;
  status: string;
  started_at: string;
  request_id?: string | null;
  episode_id?: string | null;
  task_id?: string | null;
  parent_span_id?: string | null;
  ended_at?: string | null;
  duration_ms?: number | null;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  error?: string | null;
  attributes: Record<string, unknown>;
}

export interface RuntimeEpisodeStatus {
  schema_version?: number;
  projection_level?: 'summary' | 'full' | string;
  observed_at?: string;
  updated_at?: string | null;
  episode_id?: string;
  business_episode_id?: string;
  episode?: string;
  title?: string;
  episode_ref: string;
  production_stage?: string | null;
  state_source?: string | null;
  execution_status?: string;
  blocking_reason?: string | null;
  current_action?: string | null;
  auto_recoverable?: boolean;
  needs_user?: boolean;
  next_step?: string | null;
  image_progress?: {
    expected_frames?: number;
    generated_frames?: number;
    accepted_frames?: number;
    pending_review_frames?: number;
    pending_decision_frames?: number;
    technical_failed_frames?: number;
  };
  heartbeat?: {
    at?: string | null;
    health?: string | null;
    runner_status?: string | null;
    host_loop?: string | null;
  };
  consistency_warnings?: string[];
  error?: string;
}

export interface RuntimeEpisodeStatusPage {
  items: RuntimeEpisodeStatus[];
  count: number;
  total?: number | null;
  stage_counts?: Record<string, number>;
  limit: number;
  offset: number;
  has_more: boolean;
  errors: Array<{ episode_ref: string; code: string }>;
}

export interface RuntimeEventItem {
  event_id?: string | null;
  event_type?: string | null;
  aggregate_type?: string | null;
  aggregate_id?: string | null;
  episode_id?: string | null;
  occurred_at?: string | null;
  trace_id?: string | null;
  task_id?: string | null;
}

export interface RuntimeEventPage {
  items: RuntimeEventItem[];
  count: number;
  limit: number;
  offset: number;
  has_more: boolean;
  episode_id?: string | null;
}
