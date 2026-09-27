// ─── VaultAI API Client ───────────────────────────────────────────────────
// All backend communication goes through this module.
// Configure the backend origin via NEXT_PUBLIC_API_URL (e.g. http://localhost:8000).
// Default falls back to the loopback backend for local development.

const BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const API = `${BASE}/api/v1`;

// ── Types ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;        // "ok"
  version: string;
  ollama_status: string; // "available" | "unavailable"
  ollama_model: string;
  available_models: string[];
}

export interface EvidenceItem {
  document_id: string;
  source: string;
  chunk_id: string;
  score: number;
  snippet: string;
}

export interface ChatRequest {
  message: string;
  document_ids?: string[];
  image_path?: string;
}

export interface ChatResponse {
  request_id: string;
  answer: string;
  route: string;
  model: string;
  duration_ms: number;
  evidence: EvidenceItem[];
  status: string; // "success" | "insufficient"
  generated_code?: string;
  sandbox_result?: {
    stdout: string;
    stderr: string;
    exit_code: number;
    duration_seconds: number;
    timed_out: boolean;
    error_message?: string | null;
  };
  coding_attempts?: number;
  coding_status?: string;
  vision_status?: string;
  vision_result?: { description?: string; model?: string; duration_ms?: number };
  vision_error?: string;
}

export interface DocumentMeta {
  id: string;
  filename: string;
  sha256: string;
  size_bytes: number;
  chunks_count: number;
  created_at: string;
  status: string;
}

export interface SandboxResponse {
  request_id: string;
  language: string;
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_seconds: number;
  timed_out: boolean;
  error_message?: string | null;
}

export interface AuditEvent {
  id: number;
  timestamp: string;
  employee_id: string | null;
  employee_name: string | null;
  department: string | null;
  position: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  result: string;
  details: Record<string, unknown>;
  request_id: string | null;
}
export interface AuditResponse { source: string; events: AuditEvent[]; }
export interface EmployeeIdentity {
  employee_id: string;
  full_name: string;
  department: string | null;
  position: string | null;
  is_active: boolean;
}
export interface AuthResponse { authenticated: boolean; employee: EmployeeIdentity; }
export interface AdminEmployee extends EmployeeIdentity { id: number; }
export interface AdminPosition { id: number; name: string; department_id: number | null; is_active: boolean; }
export interface AdminPermission { id: number; code: string; name: string; is_active: boolean; }

// ── API functions ─────────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body === 'object' && body !== null) {
        const detailObj = body.detail;
        if (typeof detailObj === 'object' && detailObj !== null) {
          if (detailObj.error && typeof detailObj.error.message === 'string') {
            detail = detailObj.error.message;
          } else if (typeof detailObj.message === 'string') {
            detail = detailObj.message;
          } else {
            detail = JSON.stringify(detailObj);
          }
        } else if (typeof body.detail === 'string') {
          detail = body.detail;
        } else if (typeof body.detail === 'undefined' && typeof body.detail === 'undefined') {
           // Fallback to generic body check if detail isn't there
           detail = body.message || body.error || detail;
        }
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const VaultAPI = {
  /** GET /api/v1/health */
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API}/health`, { cache: 'no-store', credentials: 'include' });
    return handleResponse<HealthResponse>(res);
  },

  /** GET /api/v1/documents */
  async listDocuments(): Promise<DocumentMeta[]> {
    const res = await fetch(`${API}/documents`, { cache: 'no-store', credentials: 'include' });
    return handleResponse<DocumentMeta[]>(res);
  },

  /** POST /api/v1/documents/upload  (PDF only) */
  async uploadDocument(file: File, okfConceptId?: string): Promise<DocumentMeta> {
    const form = new FormData();
    form.append('file', file);

    if (okfConceptId) {
      form.append('okf_concept_id', okfConceptId);
    }

    const res = await fetch(`${API}/documents`, {
      method: 'POST',
      credentials: 'include',
      body: form,
    });
    return handleResponse<DocumentMeta>(res);
  },

  /** POST /api/v1/chat */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(request),
    });
    return handleResponse<ChatResponse>(res);
  },

  async uploadVisionImage(file: File): Promise<{ image_path: string }> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API}/vision/upload`, { method: 'POST', body: form, credentials: 'include' });
    return handleResponse<{ image_path: string }>(res);
  },

  async executeSandbox(code: string): Promise<SandboxResponse> {
    const res = await fetch(`${API}/sandbox/execute`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ language: 'python', code }),
    });
    return handleResponse<SandboxResponse>(res);
  },

  async getAudit(): Promise<AuditResponse> {
    const res = await fetch(`${API}/audit`, { cache: 'no-store', credentials: 'include' });
    return handleResponse<AuditResponse>(res);
  },

  async login(employee_id: string, password: string): Promise<AuthResponse> {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ employee_id, password }),
    });
    return handleResponse<AuthResponse>(res);
  },
  async getCurrentEmployee(): Promise<AuthResponse> {
    const res = await fetch(`${API}/auth/me`, { credentials: 'include', cache: 'no-store' });
    return handleResponse<AuthResponse>(res);
  },
  async logout(): Promise<void> {
    const res = await fetch(`${API}/auth/logout`, { method: 'POST', credentials: 'include' });
    if (!res.ok) {
      await handleResponse<unknown>(res);
    }
  },
  async listAdminEmployees(): Promise<AdminEmployee[]> {
    const res = await fetch(`${API}/admin/employees`, { credentials: 'include', cache: 'no-store' });
    return handleResponse<AdminEmployee[]>(res);
  },
  async listAdminPositions(): Promise<AdminPosition[]> {
    const res = await fetch(`${API}/admin/positions`, { credentials: 'include', cache: 'no-store' });
    return handleResponse<AdminPosition[]>(res);
  },
  async listAdminPermissions(): Promise<AdminPermission[]> {
    const res = await fetch(`${API}/admin/permissions`, { credentials: 'include', cache: 'no-store' });
    return handleResponse<AdminPermission[]>(res);
  },
  async updateAdminEmployee(id: number, current_password: string, is_active: boolean): Promise<AdminEmployee> {
    const res = await fetch(`${API}/admin/employees/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ current_password, is_active }),
    });
    return handleResponse<AdminEmployee>(res);
  },
  async setPositionPermission(positionId: number, permissionId: number, current_password: string, allowed: boolean) {
    const res = await fetch(`${API}/admin/positions/${positionId}/permissions`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ current_password, permission_id: permissionId, allowed }),
    });
    return handleResponse<{ position: string; permission: string; allowed: boolean }>(res);
  },
};