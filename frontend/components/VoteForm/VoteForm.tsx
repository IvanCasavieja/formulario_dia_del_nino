'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { ApiError, castVote, getVoteCandidates, type VoteCandidate } from '@/lib/api';
import { VoteConsentCheckbox } from './VoteConsentCheckbox';
import { voteSchema, type VoteFormValues } from './validation';

function PlaceholderThumbnail({ n }: { n: number }) {
  return (
    <div className="flex aspect-video w-full items-center justify-center rounded-xl bg-gradient-to-br from-blue to-blue-deep">
      <div className="flex flex-col items-center gap-1 text-blue-light">
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-10 w-10">
          <path d="M8 5v14l11-7z" />
        </svg>
        <span className="font-display text-xs font-medium uppercase tracking-[0.2em]">Video {n}</span>
      </div>
    </div>
  );
}

export function VoteForm() {
  const [candidates, setCandidates] = useState<VoteCandidate[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [voted, setVoted] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<VoteFormValues>({
    resolver: zodResolver(voteSchema),
    defaultValues: {
      adult_first_name: '',
      adult_last_name: '',
      adult_email: '',
      video_choice: '',
      terms_accepted: false,
    },
  });

  useEffect(() => {
    let cancelled = false;
    getVoteCandidates()
      .then((data) => {
        if (!cancelled) setCandidates(data);
      })
      .catch(() => {
        // GET /api/votes/candidates takes no input, so any failure here is an internal
        // backend/Salesforce error, never something meant for a public visitor to read
        // (unlike castVote's errors below, which can be a real "you already voted").
        if (!cancelled) {
          setLoadError('No se pudieron cargar los videos. Intenta de nuevo en unos minutos.');
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedChoice = watch('video_choice');

  const onSubmit = async (values: VoteFormValues) => {
    setSubmissionError(null);
    try {
      await castVote(values);
      setVoted(true);
    } catch (error) {
      setSubmissionError(error instanceof ApiError ? error.message : 'Hubo un problema. Intenta nuevamente.');
    }
  };

  const inputClass =
    'rounded-xl border border-line bg-surface px-4 py-3 text-ink outline-none transition focus:border-blue focus:ring-2 focus:ring-blue/15';
  const labelClass = 'flex flex-col gap-2 text-sm font-medium text-ink-soft';
  const errorClass = 'text-xs font-medium text-red-deep';

  return (
    <div
      id="votacion"
      className="mx-auto w-full max-w-3xl overflow-hidden rounded-[2rem] border border-line bg-surface shadow-[0_20px_45px_-25px_rgba(36,20,23,0.35)]"
    >
      <div className="bg-blue-deep px-6 py-4 sm:px-8">
        <p className="font-display text-xs font-medium uppercase tracking-[0.3em] text-blue-light">
          Votación pública
        </p>
      </div>

      <div className="flex flex-col gap-6 p-6 sm:p-8">
        {voted ? (
          <p className="rounded-xl border border-line bg-bg p-4 text-ink">
            ¡Gracias por votar! Tu voto quedó registrado.
          </p>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
            <div>
              <h2 className="font-display text-lg font-semibold text-ink">Elegí tu video favorito</h2>
              {loadError && <p className={`mt-2 ${errorClass}`}>{loadError}</p>}
              {!loadError && candidates === null && <p className="mt-2 text-sm text-ink-soft">Cargando videos...</p>}
              {!loadError && candidates !== null && candidates.length === 0 && (
                <p className="mt-2 text-sm text-ink-soft">Todavía no hay videos habilitados para la votación pública.</p>
              )}
            </div>

            {candidates && candidates.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2">
                {candidates.map((candidate, index) => {
                  const isSelected = selectedChoice === candidate.video_choice;
                  return (
                    <label
                      key={candidate.video_choice}
                      className={`flex cursor-pointer flex-col gap-3 rounded-2xl border-2 p-3 transition ${
                        isSelected ? 'border-blue bg-blue/5' : 'border-line bg-surface hover:border-blue-light'
                      }`}
                    >
                      <input
                        type="radio"
                        value={candidate.video_choice}
                        checked={isSelected}
                        onChange={() => setValue('video_choice', candidate.video_choice, { shouldValidate: true })}
                        className="sr-only"
                      />
                      <PlaceholderThumbnail n={index + 1} />
                      <span className="text-center font-display text-sm font-medium text-ink">
                        {candidate.child_first_name} {candidate.child_last_name}
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
            {errors.video_choice && <span className={errorClass}>{errors.video_choice.message}</span>}

            <div className="ticket-notch -mx-6 sm:-mx-8" />

            <div className="grid gap-4 md:grid-cols-2">
              <label className={labelClass}>
                Tu nombre
                <input {...register('adult_first_name')} className={inputClass} />
                {errors.adult_first_name && <span className={errorClass}>{errors.adult_first_name.message}</span>}
              </label>
              <label className={labelClass}>
                Tu apellido
                <input {...register('adult_last_name')} className={inputClass} />
                {errors.adult_last_name && <span className={errorClass}>{errors.adult_last_name.message}</span>}
              </label>
            </div>

            <label className={labelClass}>
              Correo electrónico
              <input {...register('adult_email')} className={inputClass} />
              {errors.adult_email && <span className={errorClass}>{errors.adult_email.message}</span>}
            </label>

            <VoteConsentCheckbox
              checked={watch('terms_accepted')}
              onChange={(value) => setValue('terms_accepted', value, { shouldValidate: true })}
            />
            {errors.terms_accepted && <span className={errorClass}>{errors.terms_accepted.message}</span>}

            <button
              type="submit"
              disabled={isSubmitting || !candidates?.length}
              className="cursor-pointer rounded-full bg-red px-6 py-3.5 font-display font-medium text-white shadow-lg shadow-red/20 transition hover:-translate-y-0.5 hover:bg-red-deep disabled:pointer-events-none disabled:opacity-60"
            >
              {isSubmitting ? 'Enviando...' : 'Votar'}
            </button>

            {submissionError && (
              <p className="rounded-xl border border-red/20 bg-red/5 p-3 text-sm text-red-deep">{submissionError}</p>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
