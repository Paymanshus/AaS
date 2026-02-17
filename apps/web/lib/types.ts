export type ArgumentStatus = "waiting" | "running" | "completed" | "failed";
export type ArgumentPhase = "opening" | "escalation" | "resolution";

export type ArgumentShape = "QUICK_SKIRMISH" | "PROPER_THROWDOWN" | "SLOW_BURN";
export type WinCondition =
  | "BE_RIGHT"
  | "FIND_OVERLAP"
  | "EXPOSE_WEAK_POINTS"
  | "UNDERSTAND_OTHER_SIDE";
export type PaceMode = "FAST" | "NORMAL" | "DRAMATIC";
export type EvidenceMode = "FREEFORM" | "RECEIPTS_PREFERRED";

export type ArgumentControls = {
  argument_composure: number;
  argument_shape: ArgumentShape;
  win_condition: WinCondition;
  guardrails: {
    no_personal_attacks: boolean;
    no_moral_absolutism: boolean;
    no_hypotheticals: boolean;
    steelman_before_rebuttal: boolean;
    stay_on_topic: boolean;
  };
  audience_mode: boolean;
  pace_mode: PaceMode;
  evidence_mode: EvidenceMode;
};

export type Participant = {
  id: string;
  user_id: string;
  seat_order: number;
  ready: boolean;
  persona_snapshot: {
    stance: string;
    defend_points: string[];
    red_lines: string[];
  } | null;
};

export type ArgumentView = {
  id: string;
  topic: string;
  creator_user_id: string;
  status: ArgumentStatus;
  phase: ArgumentPhase;
  controls: ArgumentControls;
  turn_count: number;
  audience_mode: boolean;
  created_at: string;
  started_at: string | null;
  ended_at: string | null;
  participants: Participant[];
};

export type TurnView = {
  id: string;
  turn_index: number;
  speaker_participant_id: string;
  phase: ArgumentPhase;
  content: string;
  metrics: Record<string, unknown>;
  model_metadata: Record<string, unknown>;
  created_at: string;
};

export type TurnEvent = {
  id: number;
  argument_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  turn_index: number | null;
  created_at: string;
};

export type WrappedReport = {
  who_cooked: string;
  best_receipts: string[];
  most_stubborn_point: string;
  unexpected_common_ground: string;
  momentum_shift_turn: number | null;
  highlights: string[];
};

export type MyArgumentsResponse = {
  active: Array<{
    id: string;
    topic: string;
    status: ArgumentStatus;
    phase: ArgumentPhase;
    created_at: string;
    started_at: string | null;
    ended_at: string | null;
  }>;
  past: Array<{
    id: string;
    topic: string;
    status: ArgumentStatus;
    phase: ArgumentPhase;
    created_at: string;
    started_at: string | null;
    ended_at: string | null;
  }>;
  credits_balance: number;
};

export type ClientUser = {
  id: string;
  handle: string;
};
