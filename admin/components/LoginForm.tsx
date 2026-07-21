"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AdminApiError, adminLogin } from "@/lib/adminApi";
import { setAdminToken } from "@/lib/adminAuth";

export function LoginForm() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await adminLogin(password);
      setAdminToken(access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto flex w-full max-w-sm flex-col gap-4 rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-600">Tienda Inglesa</p>
        <h1 className="text-lg font-semibold text-zinc-900">Panel de administración</h1>
      </div>
      <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700">
        Contraseña
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded-2xl border border-zinc-300 px-4 py-3"
          autoFocus
          required
        />
      </label>
      {error && <p className="text-sm text-rose-600">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="rounded-full bg-rose-600 px-6 py-3 font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Ingresando..." : "Ingresar"}
      </button>
    </form>
  );
}
