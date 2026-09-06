// ─── VaultAI UI Types ─────────────────────────────────────────────────────────

/** A document as returned by the backend (DocumentMeta). */
export interface DocumentItem {
  id: string;       // maps to doc_id
  name: string;     // maps to filename
  chunks: number;   // maps to chunk_count
  sha256: string;
  ingestedAt: string; // maps to ingested_at
  status: string;   // "indexed" | "processing" | "error"
}

/** A grounded evidence chunk (maps to backend EvidenceItem). */
export interface GroundedChunk {
  source: string;    // filename / document source
  chunkId: string;   // chunk_id
  score: number;     // cosine similarity score
  text: string;      // snippet
  documentId?: string;
}

/** A single step in a LangGraph agent trace (UI-only, populated from route/model provenance). */
export interface AgentStep {
  step: number;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  detail: string;
}

/** Provenance info attached to a completed assistant message. */
export interface ModelProvenance {
  model: string;
  route: string;
  durationMs: number;
  requestId: string;
  status: string; // "success" | "insufficient"
}

/** A message in the chat stream. */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  route?: string;
  steps?: AgentStep[];
  evidence?: GroundedChunk[];
  provenance?: ModelProvenance;
  timestamp: string;
  error?: string;
}

export interface AuditLogItem {
  id: string;
  time: string;
  user: string;
  query: string;
  route: string;
  tools: string;
  status: string;
  output: string;
}