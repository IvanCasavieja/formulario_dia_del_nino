// TEMP copy of admin/app/jurado/page.tsx - see app/admin/layout.tsx.

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  JuradoApiError,
  type JuradoStatus,
  type VoteCandidate,
  getJuradoStatus,
  getVoteCandidates,
  juradoVote,
} from "@/lib/admin/juradoApi";
import { clearJuradoSession } from "@/lib/admin/juradoAuth";

export default function JuradoVotePage() {
  const [status, setStatus] = useState<JuradoStatus | null>(null);
  const [candidates, setCandidates] = useState<VoteCandidate[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [statusData, candidatesData] = await Promise.all([getJuradoStatus(), getVoteCandidates()]);
      setStatus(statusData);
      setCandidates(candidatesData);
    } catch (err) {
      setError(err instanceof JuradoApiError ? err.message : "Error al cargar la votación.");
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  async function onVote() {
    if (!selected) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await juradoVote(selected);
      setStatus(updated);
    } catch (err) {
      setError(err instanceof JuradoApiError ? err.message : "No se pudo registrar tu voto.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-600">Tienda Inglesa</p>
          <h1 className="text-xl font-semibold text-zinc-900">
            Voto del jurado{status ? ` — ${status.nombre}` : ""}
          </h1>
        </div>
        <button
          onClick={() => {
            clearJuradoSession();
            window.location.href = "/admin/jurado-login";
          }}
          className="text-sm text-zinc-500 hover:text-zinc-900"
        >
          Cerrar sesión
        </button>
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {!status || !candidates ? (
        <p className="text-sm text-zinc-500">Cargando...</p>
      ) : status.ha_votado ? (
        <p className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800">
          Ya emitiste tu voto. Elegiste al video de{" "}
          {candidates.find((c) => c.video_choice === status.video_elegido)?.child_first_name ?? "—"}.
        </p>
      ) : candidates.length === 0 ? (
        <p className="text-sm text-zinc-500">Todavía no hay videos habilitados para la votación.</p>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2">
            {candidates.map((candidate) => {
              const isSelected = selected === candidate.video_choice;
              return (
                <label
                  key={candidate.video_choice}
                  className={`flex cursor-pointer flex-col gap-2 rounded-2xl border-2 p-4 transition ${
                    isSelected ? "border-rose-600 bg-rose-50" : "border-zinc-200 bg-white hover:border-rose-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="video_choice"
                    value={candidate.video_choice}
                    checked={isSelected}
                    onChange={() => setSelected(candidate.video_choice)}
                    className="sr-only"
                  />
                  <span className="font-semibold text-zinc-900">
                    {candidate.child_first_name} {candidate.child_last_name}
                  </span>
                </label>
              );
            })}
          </div>
          <button
            onClick={onVote}
            disabled={!selected || submitting}
            className="rounded-full bg-rose-600 px-6 py-3 font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? "Enviando..." : "Confirmar voto"}
          </button>
        </>
      )}
    </main>
  );
}
