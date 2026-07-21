const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// Backend errors always arrive as {"detail": {"error": "...", "message": "..."}} - see
// backend/app/main.py's exception handlers - so every failure path here reads the same
// shape regardless of which endpoint or handler produced it.
async function readErrorDetail(response: Response): Promise<{ error?: string; message?: string }> {
  try {
    const body = await response.json();
    return body?.detail ?? body ?? {};
  } catch {
    return {};
  }
}

export interface CreateSubmissionPayload {
  parent_first_name: string;
  parent_last_name: string;
  parent_cedula: string;
  parent_email: string;
  parent_phone: string;
  child_full_name: string;
  child_cedula: string;
  video_content_type: string;
  video_declared_size_bytes: number;
  video_declared_duration_seconds: number;
  terms_accepted: boolean;
  terms_version: string;
}

export interface CreateSubmissionResponse {
  submission_id: string;
  upload_url: string;
  upload_token: string;
  video_key: string;
  expires_in: number;
}

export async function createSubmission(payload: CreateSubmissionPayload): Promise<CreateSubmissionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/submissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(response.status, detail.message ?? "No se pudo enviar el formulario.", detail.error);
  }
  return response.json();
}

export async function confirmUpload(submissionId: string, uploadToken: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/submissions/${submissionId}/confirm-upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${uploadToken}` },
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiError(response.status, detail.message ?? "No se pudo confirmar la subida del video.", detail.error);
  }
}
