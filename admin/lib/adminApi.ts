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
  id: string;
  parent_first_name: string;
  parent_last_name: string;
  child_full_name: string;
  status: string;
  created_at: string;
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
  child_cedula: string;
  video_content_type: string;
  video_actual_size_bytes: number | null;
  video_duration_seconds: number | null;
  moderation_result: Record<string, unknown> | null;
  admin_notes: string | null;
  admin_reviewed_by: string | null;
  admin_decided_at: string | null;
  terms_accepted: boolean;
  terms_version: string;
  video_view_url: string | null;
  salesforce_synced_at: string | null;
  salesforce_sync_error: string | null;
}

export async function getSubmissionDetail(id: string): Promise<AdminSubmissionDetail> {
  const response = await adminFetch(`/api/admin/submissions/${id}`);
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new AdminApiError(response.status, detail.message ?? "No se pudo cargar el detalle.", detail.error);
  }
  return response.json();
}

export async function decideSubmission(
  id: string,
  decision: "approved" | "rejected",
  note?: string,
  reviewedBy?: string,
): Promise<AdminSubmissionDetail> {
  const response = await adminFetch(`/api/admin/submissions/${id}/decision`, {
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
