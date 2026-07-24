// TEMP copy of admin/lib/adminAuth.ts - see app/admin/layout.tsx.

// sessionStorage, not a cookie: this app and the backend (Render) are different
// origins, so a cookie would need cross-site SameSite=None/Secure handling for no
// real benefit here. This is UX-only gating - the backend's require_admin dependency
// on every /api/admin/* route is the actual enforcement.
const TOKEN_KEY = "admin_token";

export function getAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAdminToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAdminToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}
