// TEMP copy of admin/app/dashboard/resultados/page.tsx - see app/admin/layout.tsx.

"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AdminApiError, type ResultadosResponse, getResultadosVotacion } from "@/lib/admin/adminApi";

export default function ResultadosPage() {
  const [data, setData] = useState<ResultadosResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await getResultadosVotacion());
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Error al cargar los resultados.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  const videosOrdenados = data ? [...data.videos].sort((a, b) => b.puntaje_final - a.puntaje_final) : [];

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-600">Tienda Inglesa</p>
          <h1 className="text-xl font-semibold text-zinc-900">Resultados de la votación</h1>
        </div>
        <div className="flex items-center gap-4">
          <button onClick={refresh} disabled={loading} className="text-sm text-zinc-500 hover:text-zinc-900">
            {loading ? "Actualizando..." : "Actualizar"}
          </button>
          <Link href="/admin/dashboard" className="text-sm text-zinc-500 hover:text-zinc-900">
            Volver
          </Link>
        </div>
      </div>

      {error && <p className="text-sm text-rose-600">{error}</p>}

      {data && (
        <>
          <div className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-50 text-zinc-500">
                <tr>
                  <th className="px-4 py-3">Niño/a</th>
                  <th className="px-4 py-3">Votos jurado</th>
                  <th className="px-4 py-3">Votos público</th>
                  <th className="px-4 py-3">Punto público</th>
                  <th className="px-4 py-3">Puntaje final</th>
                </tr>
              </thead>
              <tbody>
                {videosOrdenados.map((video) => (
                  <tr key={video.video_choice} className="border-t border-zinc-100">
                    <td className="px-4 py-3 font-medium text-zinc-900">
                      {video.child_first_name} {video.child_last_name}
                    </td>
                    <td className="px-4 py-3">{video.votos_jurado}</td>
                    <td className="px-4 py-3">{video.votos_publico}</td>
                    <td className="px-4 py-3">{video.punto_publico}</td>
                    <td className="px-4 py-3 font-semibold text-rose-600">{video.puntaje_final}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Estado del jurado
            </h2>
            <ul className="flex flex-wrap gap-2">
              {data.jurados.map((jurado) => (
                <li
                  key={jurado.jurado_id}
                  className={`rounded-full border px-3 py-1 text-sm ${
                    jurado.ha_votado ? "border-emerald-300 bg-emerald-50 text-emerald-800" : "border-zinc-300 bg-white text-zinc-700"
                  }`}
                >
                  {jurado.nombre || jurado.jurado_id} {jurado.ha_votado ? "✓ votó" : "— falta"}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </main>
  );
}
