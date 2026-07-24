// TEMP copy of admin/components/JuradoLoginForm.tsx - see app/admin/layout.tsx.

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { JuradoApiError, juradoLogin } from "@/lib/admin/juradoApi";
import { setJuradoSession } from "@/lib/admin/juradoAuth";

export function JuradoLoginForm() {
  const router = useRouter();
  const [juradoId, setJuradoId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token, nombre } = await juradoLogin(juradoId, password);
      setJuradoSession(access_token, nombre);
      router.push("/admin/jurado");
    } catch (err) {
      setError(err instanceof JuradoApiError ? err.message : "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="mx-auto flex w-full max-w-sm flex-col gap-4 rounded-3xl border border-zinc-200 bg-white p-8 shadow-sm">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-600">Tienda Inglesa</p>
        <h1 className="text-lg font-semibold text-zinc-900">Panel del jurado</h1>
      </div>
      <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700">
        Usuario
        <input
          value={juradoId}
          onChange={(event) => setJuradoId(event.target.value)}
          className="rounded-2xl border border-zinc-300 px-4 py-3"
          autoFocus
          required
        />
      </label>
      <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700">
        Contraseña
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="rounded-2xl border border-zinc-300 px-4 py-3"
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
