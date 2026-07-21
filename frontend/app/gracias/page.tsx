import Link from "next/link";

export default function GraciasPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg px-4 py-16 sm:px-6 lg:px-8">
      <div className="w-full max-w-md overflow-hidden rounded-[2rem] border border-line bg-surface shadow-[0_20px_45px_-25px_rgba(36,20,23,0.35)]">
        <div className="bg-blue-deep px-8 py-5">
          <p className="font-display text-xs font-medium tracking-[0.3em] text-blue-light uppercase">Inscripción confirmada</p>
        </div>
        <div className="ticket-notch -mt-px" />
        <div className="px-8 py-8">
          <h1 className="font-display text-3xl font-semibold text-ink">¡Ya estás participando!</h1>
          <p className="mt-4 text-ink-soft">
            El video quedó en proceso de revisión y la moderación continuará en segundo plano. Te avisamos por mail si resultó ganador.
          </p>
          <Link
            href="/"
            className="mt-8 inline-flex rounded-full bg-red px-6 py-3 font-display font-medium text-white transition hover:bg-red-deep"
          >
            Volver al inicio
          </Link>
        </div>
      </div>
    </main>
  );
}
