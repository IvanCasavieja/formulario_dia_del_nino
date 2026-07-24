import { clearJuradoSession, getJuradoToken } from "./juradoAuth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class JuradoApiError extends Error {
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

async function juradoFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getJuradoToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    clearJuradoSession();
    if (typeof window !== "undefined") {
      window.location.href = "/jurado-login";
    }
  }

  return response;
}

export interface JuradoLoginResponse {
  access_token: string;
  expires_in: number;
  nombre: string;
}

export async function juradoLogin(juradoId: string, password: string): Promise<JuradoLoginResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jurado/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jurado_id: juradoId, password }),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new JuradoApiError(response.status, detail.message ?? "Usuario o contraseña incorrectos.", detail.error);
  }
  return response.json();
}

export interface JuradoStatus {
  nombre: string;
  ha_votado: boolean;
  video_elegido: string | null;
}

export async function getJuradoStatus(): Promise<JuradoStatus> {
  const response = await juradoFetch("/api/jurado/status");
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new JuradoApiError(response.status, detail.message ?? "No se pudo cargar tu estado.", detail.error);
  }
  return response.json();
}

export interface VoteCandidate {
  video_choice: string;
  child_first_name: string;
  child_last_name: string;
}

// Public, unauthenticated endpoint - same one the public /votar page reads. No
// juradoFetch wrapper needed (no token, no 401-redirect behavior).
export async function getVoteCandidates(): Promise<VoteCandidate[]> {
  const response = await fetch(`${API_BASE_URL}/api/votes/candidates`);
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new JuradoApiError(response.status, detail.message ?? "No se pudieron cargar los videos.", detail.error);
  }
  const data = await response.json();
  return data.candidates;
}

export async function juradoVote(videoChoice: string): Promise<JuradoStatus> {
  const response = await juradoFetch("/api/jurado/vote", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ video_choice: videoChoice }),
  });
  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new JuradoApiError(response.status, detail.message ?? "No se pudo registrar tu voto.", detail.error);
  }
  return response.json();
}
