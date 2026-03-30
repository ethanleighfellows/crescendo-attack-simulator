export interface RunConfig {
  objective: string;
  vulnerability: string;
  vulnerability_type: string;
  initial_prompt: string | null;
  system_prompt_override: string | null;

  max_rounds: number;
  max_backtracks: number;
  enhancement_probability: number;
  success_threshold: number;
  stop_on_first_success: boolean;
  turn_level_attacks: string[];

  simulator_provider: string;
  simulator_model: string;
  simulator_api_key: string | null;
  simulator_base_url: string | null;

  target_provider: string;
  target_model: string;
  target_api_key: string | null;
  target_base_url: string | null;

  temperature: number;
  max_retries: number;
}

export interface JudgeDecision {
  value: boolean;
  rationale: string;
  metadata: number;
  description?: string;
}

export interface TurnRecord {
  round_number: number;
  backtrack_count: number;
  user_prompt: string;
  assistant_response: string;
  turn_level_attack: string | null;
  enhancement_applied: boolean;
  refusal_decision: JudgeDecision | null;
  eval_decision: JudgeDecision | null;
  is_backtrack: boolean;
  timestamp: string;
}

export interface RunResult {
  run_id: string;
  config: RunConfig;
  status: string;
  outcome: string | null;
  turns: TurnRecord[];
  total_rounds: number;
  total_backtracks: number;
  final_eval_score: number | null;
  started_at: string | null;
  completed_at: string | null;
  error: string | null;
}

export interface TurnEvent {
  event_type: string;
  run_id: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export type AppPhase = 'setup' | 'running' | 'review' | 'export';

export type PresetName = 'conservative' | 'balanced' | 'aggressive' | 'custom';

export interface Preset {
  max_rounds: number;
  max_backtracks: number;
  enhancement_probability: number;
  success_threshold: number;
  stop_on_first_success: boolean;
  turn_level_attacks: string[];
}

export const DEFAULT_CONFIG: RunConfig = {
  objective: '',
  vulnerability: '',
  vulnerability_type: '',
  initial_prompt: null,
  system_prompt_override: null,
  max_rounds: 10,
  max_backtracks: 10,
  enhancement_probability: 0.5,
  success_threshold: 100,
  stop_on_first_success: true,
  turn_level_attacks: [],
  simulator_provider: 'together',
  simulator_model: 'meta-llama/Meta-Llama-3-8B-Instruct-Lite',
  simulator_api_key: null,
  simulator_base_url: null,
  target_provider: 'together',
  target_model: 'meta-llama/Meta-Llama-3-8B-Instruct-Lite',
  target_api_key: null,
  target_base_url: null,
  temperature: 0.7,
  max_retries: 3,
};
