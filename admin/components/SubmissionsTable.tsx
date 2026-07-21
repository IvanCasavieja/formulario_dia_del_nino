"use client";

import type { AdminSubmissionListItem } from "@/lib/adminApi";

interface Props {
  submissions: AdminSubmissionListItem[];
  onSelect: (id: string) => void;
}

export function SubmissionsTable({ submissions, onSelect }: Props) {
  if (submissions.length === 0) {
    return <p className="text-sm text-zinc-500">No hay inscripciones en este estado.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-zinc-200 bg-white">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-200 text-zinc-500">
            <th className="px-4 py-3 font-medium">Niño/a</th>
            <th className="px-4 py-3 font-medium">Padre/Madre</th>
            <th className="px-4 py-3 font-medium">Estado</th>
            <th className="px-4 py-3 font-medium">Fecha</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {submissions.map((submission) => (
            <tr key={submission.id} className="border-b border-zinc-100 last:border-0">
              <td className="px-4 py-3">{submission.child_full_name}</td>
              <td className="px-4 py-3">
                {submission.parent_first_name} {submission.parent_last_name}
              </td>
              <td className="px-4 py-3">
                <span className="rounded-full bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                  {submission.status}
                </span>
              </td>
              <td className="px-4 py-3 text-zinc-500">
                {new Date(submission.created_at).toLocaleString("es-UY")}
              </td>
              <td className="px-4 py-3 text-right">
                <button onClick={() => onSelect(submission.id)} className="font-medium text-rose-600 hover:underline">
                  Ver
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
