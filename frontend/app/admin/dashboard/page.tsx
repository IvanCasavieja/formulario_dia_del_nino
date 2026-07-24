// TEMP copy of admin/app/dashboard/page.tsx - see app/admin/layout.tsx.

"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { SubmissionDetail } from "@/components/admin/SubmissionDetail";
import { SubmissionsTable } from "@/components/admin/SubmissionsTable";
import { AdminApiError, type AdminSubmissionListItem, listSubmissions } from "@/lib/admin/adminApi";
import { clearAdminToken } from "@/lib/admin/adminAuth";

const STATUS_OPTIONS = [
  "needs_review",
  "pending_upload",
  "uploaded",
  "processing",
  "approved",
  "rejected",
  "failed",
  "expired",
];

export default function AdminDashboardPage() {
  const [status, setStatus] = useState("needs_review");
  const [submissions, setSubmissions] = useState<AdminSubmissionListItem[]>([]);
  const [selectedCedula, setSelectedCedula] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setSubmissions(await listSubmissions(status));
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Error al cargar la lista.");
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => {
    // Standard fetch-on-mount/on-filter-change pattern: `refresh` sets loading/error/
    // list state itself. There's no derived-state alternative here (data comes from
    // the network), so this is the legitimate "sync with an external system" case the
    // lint rule's own docs carve out, not the "should've just computed this" case it's
    // meant to catch.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-600">Tienda Inglesa</p>
          <h1 className="text-xl font-semibold text-zinc-900">Revisión de videos</h1>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/admin/dashboard/resultados" className="text-sm text-zinc-500 hover:text-zinc-900">
            Resultados de votación
          </Link>
          <Link href="/admin/jurado-login" className="text-sm text-zinc-500 hover:text-zinc-900">
            Panel del jurado
          </Link>
          <button
            onClick={() => {
              clearAdminToken();
              window.location.href = "/admin/login";
            }}
            className="text-sm text-zinc-500 hover:text-zinc-900"
          >
            Cerrar sesión
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {STATUS_OPTIONS.map((option) => (
          <button
            key={option}
            onClick={() => setStatus(option)}
            className={`rounded-full border px-3 py-1 text-sm transition ${
              status === option ? "border-rose-600 bg-rose-600 text-white" : "border-zinc-300 bg-white text-zinc-700"
            }`}
          >
            {option}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-zinc-500">Cargando...</p>}
      {error && <p className="text-sm text-rose-600">{error}</p>}

      <SubmissionsTable submissions={submissions} onSelect={setSelectedCedula} />

      {selectedCedula && (
        <SubmissionDetail
          key={selectedCedula}
          childCedula={selectedCedula}
          onClose={() => setSelectedCedula(null)}
          onDecided={() => {
            setSelectedCedula(null);
            refresh();
          }}
        />
      )}
    </main>
  );
}
