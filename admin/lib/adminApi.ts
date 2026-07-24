import { clearAdminToken, getAdminToken } from "./adminAuth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class AdminApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function readErrorDetail(response: Response): Promise<{ error?: string; message?: string }> {
  try {
    const body = await response.json();
    return body?.detail ?? body ?? {};
  } catch {
    return {};
  }
}

async function adminFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getAdminToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    clearAdminToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return response;
}

export async function adminLogin(password: string): Promise<{ access_token: string; expires_in: number }> {
  const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(response.status, detail.message ?? "Contraseña incorrecta.", detail.error);
  }
  return response.json();
}

export interface AdminSubmissionListItem {
  // Cedula_Nino - the child's cedula. There's no separate internal id anymore:
  // Salesforce is the only store, and this is the Data Extension's primary key.
  child_cedula: string;
  parent_first_name: string;
  parent_last_name: string;
  child_first_name: string;
  child_last_name: string;
  status: string;
  is_vote_candidate: boolean;
}

export async function listSubmissions(status?: string): Promise<AdminSubmissionListItem[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await adminFetch(`/api/admin/submissions${query}`);
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(response.status, detail.message ?? "No se pudo cargar la lista.", detail.error);
  }
  return response.json();
}

export interface AdminSubmissionDetail extends AdminSubmissionListItem {
  parent_cedula: string;
  parent_email: string;
  parent_phone: string;
  moderation_result: string | null;
  admin_notes: string | null;
  admin_reviewed_by: string | null;
  terms_accepted: boolean;
  video_key: string | null;
  video_view_url: string | null;
}

export async function getSubmissionDetail(childCedula: string): Promise<AdminSubmissionDetail> {
  const response = await adminFetch(`/api/admin/submissions/${childCedula}`);
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(response.status, detail.message ?? "No se pudo cargar el detalle.", detail.error);
  }
  return response.json();
}

export async function decideSubmission(
  childCedula: string,
  decision: "approved" | "rejected",
  note?: string,
  reviewedBy?: string,
): Promise<AdminSubmissionDetail> {
  const response = await adminFetch(`/api/admin/submissions/${childCedula}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, note, reviewed_by: reviewedBy }),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(response.status, detail.message ?? "No se pudo guardar la decisión.", detail.error);
  }
  return response.json();
}

export interface ResultadoVideo {
  video_choice: string;
  child_first_name: string;
  child_last_name: string;
  votos_jurado: number;
  votos_publico: number;
  punto_publico: number;
  puntaje_final: number;
}

export interface JuradoResultadoItem {
  jurado_id: string;
  nombre: string;
  ha_votado: boolean;
}

export interface ResultadosResponse {
  videos: ResultadoVideo[];
  jurados: JuradoResultadoItem[];
}

export async function getResultadosVotacion(): Promise<ResultadosResponse> {
  const response = await adminFetch("/api/admin/votacion/resultados");
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(response.status, detail.message ?? "No se pudieron cargar los resultados.", detail.error);
  }
  return response.json();
}

export async function setVotingCandidate(childCedula: string, enabled: boolean): Promise<AdminSubmissionDetail> {
  const response = await adminFetch(`/api/admin/submissions/${childCedula}/voting-candidate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(
      response.status,
      detail.message ?? "No se pudo actualizar la votación pública.",
      detail.error,
    );
  }
  return response.json();
}
