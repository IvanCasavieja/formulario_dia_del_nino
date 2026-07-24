// TEMP copy of admin/lib/juradoAuth.ts - see app/admin/layout.tsx.

// Same sessionStorage-not-cookie reasoning as adminAuth.ts, but its own key so a
// jurado session and a marketing-admin session don't collide if both are ever open in
// the same browser. UX-only gating - app/jurado's require_jurado dependency on the
// backend is the actual enforcement.
const TOKEN_KEY = "jurado_token";
const NOMBRE_KEY = "jurado_nombre";

export function getJuradoToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setJuradoSession(token: string, nombre: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(NOMBRE_KEY, nombre);
}

export function getJuradoNombre(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(NOMBRE_KEY);
}

export function clearJuradoSession(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(NOMBRE_KEY);
}
