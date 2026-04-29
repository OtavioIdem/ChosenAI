export type SourceItem = {
  title: string;
  source_identifier: string;
  chunk_index: number;
  score: number;
  excerpt: string;
  metadata: Record<string, unknown>;
};

export type ChatResponse = {
  answer: string;
  sources: SourceItem[];
  warnings: string[];
  mode: string;
  session_id: string;
  user_message_id: string;
  assistant_message_id: string;
  confidence_score: number;
  confidence_status: "high" | "medium" | "low";
  knowledge_gap_id?: string | null;
};

export type KnowledgeStats = {
  sources_count: number;
  chunks_count: number;
  indexed_files: string[];
};

export type FeedbackPayload = {
  message_id: string;
  rating: "useful" | "not_useful" | "incomplete" | "incorrect" | "bad_source" | "needs_adjustment";
  comment?: string;
  created_by?: string;
  create_training_candidate?: boolean;
};

export type FeedbackResponse = {
  id: string;
  message_id: string;
  rating: string;
  comment?: string | null;
  created_by?: string | null;
  training_candidate_id?: string | null;
  created_at: string;
};
