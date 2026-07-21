"use client";

import { useEffect, useState } from "react";
import {
  AdminApiError,
  type AdminSubmissionDetail as AdminSubmissionDetailType,
  decideSubmission,
  getSubmissionDetail,
} from "@/lib/adminApi";

interface Props {
  submissionId: string;
  onClose: () => void;
  onDecided: () => void;
}

export function SubmissionDetail({ submissionId, onClose, onDecided }: Props) {
  const [detail, setDetail] = useState<AdminSubmissionDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [reviewedBy, setReviewedBy] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // No reset of `detail`/`error` here on purpose: the parent renders this component
    // with `key={submissionId}`, so switching rows remounts it with fresh state
    // instead of needing an imperative reset (which would otherwise be a synchronous
    // setState call sitting directly in the effect body).
    let cancelled = false;
    getSubmissionDetail(submissionId)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof AdminApiError ? err.message : "Error al cargar el detalle.");
      });
    return () => {
      cancelled = true;
    };
  }, [submissionId]);

  async function decide(decision: "approved" | "rejected") {
    setSaving(true);
    setError(null);
    try {
      await decideSubmission(submissionId, decision, note || undefined, reviewedBy || undefined);
      onDecided();
    } catch (err) {
      setError(err instanceof AdminApiError ? err.message : "Error al guardar la decisión.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex max-h-[90vh] w-full max-w-lg flex-col gap-4 overflow-y-auto rounded-3xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-zinc-900">Detalle de inscripción</h2>
          <button onClick={onClose} className="text-sm text-zinc-500 hover:text-zinc-900">
            Cerrar
          </button>
        </div>

        {error && <p className="text-sm text-rose-600">{error}</p>}

        {!detail ? (
          <p className="text-sm text-zinc-500">Cargando...</p>
        ) : (
          <>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <dt className="text-zinc-500">Niño/a</dt>
              <dd className="text-zinc-900">
                {detail.child_full_name} ({detail.child_cedula})
              </dd>
              <dt className="text-zinc-500">Padre/Madre</dt>
              <dd className="text-zinc-900">
                {detail.parent_first_name} {detail.parent_last_name} ({detail.parent_cedula})
              </dd>
              <dt className="text-zinc-500">Email</dt>
              <dd className="text-zinc-900">{detail.parent_email}</dd>
              <dt className="text-zinc-500">Teléfono</dt>
              <dd className="text-zinc-900">{detail.parent_phone}</dd>
              <dt className="text-zinc-500">Estado</dt>
              <dd className="text-zinc-900">{detail.status}</dd>
              <dt className="text-zinc-500">Duración del video</dt>
              <dd className="text-zinc-900">
                {detail.video_duration_seconds ? `${detail.video_duration_seconds.toFixed(1)}s` : "-"}
              </dd>
              <dt className="text-zinc-500">Salesforce</dt>
              <dd className={detail.salesforce_sync_error ? "text-rose-600" : "text-zinc-900"}>
                {detail.salesforce_synced_at
                  ? `Sincronizado (${new Date(detail.salesforce_synced_at).toLocaleString("es-UY")})`
                  : detail.salesforce_sync_error
                    ? `Error: ${detail.salesforce_sync_error}`
                    : "Pendiente / no habilitado"}
              </dd>
            </dl>

            {detail.video_view_url ? (
              <video controls className="w-full rounded-2xl" src={detail.video_view_url} />
            ) : (
              <p className="text-xs text-zinc-500">
                El video todavía no tiene una vista previa disponible (subida no confirmada o expirada).
              </p>
            )}

            {detail.moderation_result && (
              <details className="rounded-2xl bg-zinc-50 p-3 text-xs text-zinc-600">
                <summary className="cursor-pointer font-medium text-zinc-700">Resultado de moderación</summary>
                <pre className="mt-2 whitespace-pre-wrap">{JSON.stringify(detail.moderation_result, null, 2)}</pre>
              </details>
            )}

            <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700">
              Notas (opcional)
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                className="rounded-2xl border border-zinc-300 px-4 py-2"
                rows={2}
              />
            </label>
            <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700">
              Revisado por (opcional)
              <input
                value={reviewedBy}
                onChange={(event) => setReviewedBy(event.target.value)}
                className="rounded-2xl border border-zinc-300 px-4 py-2"
              />
            </label>

            <div className="flex gap-3">
              <button
                onClick={() => decide("approved")}
                disabled={saving}
                className="flex-1 rounded-full bg-emerald-600 px-4 py-3 font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Aprobar
              </button>
              <button
                onClick={() => decide("rejected")}
                disabled={saving}
                className="flex-1 rounded-full bg-rose-600 px-4 py-3 font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Rechazar
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
