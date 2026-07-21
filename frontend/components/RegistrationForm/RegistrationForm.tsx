'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { ApiError, confirmUpload, createSubmission } from '@/lib/api';
import { resolveVideoContentType, validationConstants } from '@/lib/validationConstants';
import { ConsentCheckbox } from './ConsentCheckbox';
import { useUploadWithProgress } from './useUploadWithProgress';
import { registrationSchema, type RegistrationFormValues } from './validation';

const TERMS_VERSION = 'placeholder-v1';

async function parseVideoFile(file: File) {
  return await new Promise<{ duration: number }>((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'metadata';
    const url = URL.createObjectURL(file);
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve({ duration: video.duration });
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('No se pudo leer el video'));
    };
    video.src = url;
  });
}

export function RegistrationForm() {
  const router = useRouter();
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegistrationFormValues>({
    resolver: zodResolver(registrationSchema),
    defaultValues: {
      terms_accepted: false,
      terms_version: TERMS_VERSION,
    },
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [resolvedContentType, setResolvedContentType] = useState<string | null>(null);
  const [videoMessage, setVideoMessage] = useState<string | null>(null);
  const [videoRequiredError, setVideoRequiredError] = useState<string | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const { progress, isUploading, upload } = useUploadWithProgress();

  const videoHint = useMemo(() => {
    if (!selectedFile) return 'Selecciona un video mp4, mov o webm (máx. 60s, 200MB).';
    return `${selectedFile.name} · ${Math.round(selectedFile.size / (1024 * 1024))} MB`;
  }, [selectedFile]);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    setSelectedFile(null);
    setResolvedContentType(null);
    setVideoRequiredError(null);
    if (!file) {
      setVideoMessage(null);
      return;
    }

    setVideoMessage(null);
    try {
      // Some browsers (notably Safari/iOS for .mov) leave File.type empty, so the
      // content-type has to be resolvable from the file extension too - this is the
      // exact same value that must later be sent as the PUT's Content-Type header,
      // since R2's presigned URL signature is pinned to it.
      const contentType = resolveVideoContentType(file);
      if (!contentType) {
        throw new Error('Formato de video no soportado. Usa MP4, MOV o WEBM.');
      }

      const info = await parseVideoFile(file);
      const isWithinSize = file.size <= validationConstants.MAX_VIDEO_SIZE_BYTES;
      const isWithinDuration =
        info.duration <=
        validationConstants.MAX_VIDEO_DURATION_SECONDS + validationConstants.MAX_VIDEO_DURATION_TOLERANCE_SECONDS;

      if (!isWithinSize) {
        throw new Error('El video supera el límite de 200 MB');
      }
      if (!isWithinDuration) {
        throw new Error(`El video no puede superar los ${validationConstants.MAX_VIDEO_DURATION_SECONDS} segundos`);
      }

      setSelectedFile(file);
      setResolvedContentType(contentType);
      setValue('video_content_type', contentType, { shouldValidate: true });
      setValue('video_declared_size_bytes', file.size, { shouldValidate: true });
      setValue('video_declared_duration_seconds', info.duration, { shouldValidate: true });
      setVideoMessage('Video listo para subir.');
    } catch (error) {
      setSelectedFile(null);
      setResolvedContentType(null);
      setVideoMessage(error instanceof Error ? error.message : 'No se pudo validar el video');
    }
  };

  const onSubmit = async (values: RegistrationFormValues) => {
    setSubmissionError(null);

    // The video fields live in the same zod schema as the rest of the form so a
    // missing/invalid video blocks handleSubmit like any other field - but zod's
    // generic "required" message on those hidden fields would otherwise say nothing
    // useful to the user, so this is surfaced as its own explicit message instead.
    if (!selectedFile || !resolvedContentType) {
      setVideoRequiredError('Debes seleccionar un video para continuar.');
      return;
    }
    setVideoRequiredError(null);

    try {
      const created = await createSubmission(values);
      await upload(created.upload_url, selectedFile, resolvedContentType);
      await confirmUpload(created.submission_id, created.upload_token);
      router.push('/gracias');
    } catch (error) {
      setSubmissionError(error instanceof ApiError ? error.message : 'Hubo un problema. Intenta nuevamente.');
    }
  };

  const inputClass =
    'rounded-xl border border-line bg-surface px-4 py-3 text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/15';
  const labelClass = 'flex flex-col gap-2 text-sm font-medium text-ink-soft';
  const errorClass = 'text-xs font-medium text-brand-deep';

  function SectionHeading({ n, title }: { n: string; title: string }) {
    return (
      <div className="flex items-center gap-3">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand font-display text-sm font-semibold text-cream">
          {n}
        </span>
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
      </div>
    );
  }

  function Divider() {
    return <div className="ticket-notch -mx-6 sm:-mx-8" />;
  }

  return (
    <div
      id="formulario"
      className="mx-auto w-full max-w-3xl overflow-hidden rounded-[2rem] border border-line bg-surface shadow-[0_20px_45px_-25px_rgba(36,20,23,0.35)]"
    >
      <div className="bg-brand-deep px-6 py-4 sm:px-8">
        <p className="font-display text-xs font-medium uppercase tracking-[0.3em] text-sun">Formulario de inscripción</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6 p-6 sm:p-8">
        <SectionHeading n="1" title="Quién completa el formulario" />

        <div className="grid gap-4 md:grid-cols-2">
          <label className={labelClass}>
            Nombre del padre/madre/tutor
            <input {...register('parent_first_name')} className={inputClass} />
            {errors.parent_first_name && <span className={errorClass}>{errors.parent_first_name.message}</span>}
          </label>
          <label className={labelClass}>
            Apellido
            <input {...register('parent_last_name')} className={inputClass} />
            {errors.parent_last_name && <span className={errorClass}>{errors.parent_last_name.message}</span>}
          </label>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className={labelClass}>
            Cédula del padre/madre/tutor
            <input {...register('parent_cedula')} className={inputClass} />
            {errors.parent_cedula && <span className={errorClass}>{errors.parent_cedula.message}</span>}
          </label>
          <label className={labelClass}>
            Correo electrónico
            <input {...register('parent_email')} className={inputClass} />
            {errors.parent_email && <span className={errorClass}>{errors.parent_email.message}</span>}
          </label>
        </div>

        <label className={labelClass}>
          Teléfono
          <input {...register('parent_phone')} className={inputClass} />
          {errors.parent_phone && <span className={errorClass}>{errors.parent_phone.message}</span>}
        </label>

        <Divider />
        <SectionHeading n="2" title="Sobre el niño o niña" />

        <div className="grid gap-4 md:grid-cols-2">
          <label className={labelClass}>
            Nombre del niño o niña
            <input {...register('child_full_name')} className={inputClass} />
            {errors.child_full_name && <span className={errorClass}>{errors.child_full_name.message}</span>}
          </label>
          <label className={labelClass}>
            Cédula del menor
            <input {...register('child_cedula')} className={inputClass} />
            {errors.child_cedula && <span className={errorClass}>{errors.child_cedula.message}</span>}
          </label>
        </div>

        <Divider />
        <SectionHeading n="3" title="El video" />

        <label className={labelClass}>
          Subí el video
          <input
            type="file"
            accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm"
            onChange={handleFileChange}
            className={`${inputClass} file:mr-4 file:rounded-full file:border-0 file:bg-brand file:px-4 file:py-2 file:font-display file:text-sm file:font-medium file:text-cream file:transition hover:file:bg-brand-deep`}
          />
          <span className="text-xs text-ink-soft">{videoHint}</span>
          {videoMessage && <span className={errorClass}>{videoMessage}</span>}
          {videoRequiredError && <span className={errorClass}>{videoRequiredError}</span>}
        </label>

        <div className="rounded-xl border border-line bg-bg p-4 text-sm text-ink-soft">
          <p className="font-display font-medium text-ink">Validaciones aplicadas</p>
          <p className="tabular-nums">
            Duración máxima: {validationConstants.MAX_VIDEO_DURATION_SECONDS}s · Tamaño máximo:{' '}
            {Math.round(validationConstants.MAX_VIDEO_SIZE_BYTES / (1024 * 1024))} MB
          </p>
          {isUploading && (
            <div className="mt-3 space-y-1.5">
              <div className="h-2 overflow-hidden rounded-full bg-line">
                <div
                  className="h-full rounded-full bg-brand transition-[width]"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="tabular-nums text-xs text-ink-soft">Subiendo el video... {progress}%</p>
            </div>
          )}
        </div>

        <Divider />

        <ConsentCheckbox
          checked={watch('terms_accepted')}
          onChange={(value) => setValue('terms_accepted', value, { shouldValidate: true })}
        />
        {errors.terms_accepted && <span className={errorClass}>{errors.terms_accepted.message}</span>}

        <button
          type="submit"
          disabled={isSubmitting || isUploading}
          className="rounded-full bg-brand px-6 py-3.5 font-display font-medium text-cream shadow-lg shadow-brand/20 transition hover:-translate-y-0.5 hover:bg-brand-deep disabled:pointer-events-none disabled:opacity-60"
        >
          {isSubmitting || isUploading ? 'Procesando...' : 'Enviar participación'}
        </button>

        {submissionError && (
          <p className="rounded-xl border border-brand/20 bg-brand/5 p-3 text-sm text-brand-deep">{submissionError}</p>
        )}
      </form>
    </div>
  );
}
