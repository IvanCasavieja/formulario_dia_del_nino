import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { RegistrationForm } from "@/components/RegistrationForm/RegistrationForm";

const STEPS = [
  { n: "1", title: "Completá tus datos", detail: "Los tuyos y los de tu hijo o hija, en un minuto." },
  { n: "2", title: "Subí el video", detail: "Hasta 60 segundos contando por qué se merece ganar." },
  { n: "3", title: "Esperá el sorteo", detail: "Te avisamos por mail si resultó ganador." },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-bg text-ink">
      <Header />

      <section className="relative overflow-hidden bg-brand-deep">
        <div
          aria-hidden
          className="animate-float-soft pointer-events-none absolute -top-20 -left-16 h-64 w-64 rounded-full bg-sun/25 blur-2xl"
        />
        <div
          aria-hidden
          className="animate-float-soft-delay pointer-events-none absolute top-10 -right-20 h-72 w-72 rounded-full bg-teal/25 blur-2xl"
        />
        <div
          aria-hidden
          className="animate-float-soft pointer-events-none absolute bottom-[-4rem] left-1/3 h-40 w-40 rounded-full bg-cream/10 blur-xl"
        />

        <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-10 px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="max-w-3xl space-y-5">
            <p className="font-display text-sm font-medium tracking-[0.3em] text-sun uppercase">Sorteo Día del Niño</p>
            <h1 className="text-balance font-display text-4xl leading-[1.05] font-semibold text-cream sm:text-5xl lg:text-6xl">
              Contanos por qué tu hijo o hija se merece ganar.
            </h1>
            <p className="max-w-xl text-lg text-cream/80">
              Grabá un video cortito, completá el formulario y quedá participando del sorteo de Tienda Inglesa por el Día del Niño.
            </p>
          </div>

          <a
            href="#formulario"
            className="inline-flex w-fit items-center gap-2 rounded-full bg-brand px-7 py-3.5 font-display font-medium text-cream shadow-lg shadow-black/20 transition hover:-translate-y-0.5 hover:bg-sun hover:text-brand-deep"
          >
            Quiero participar
          </a>

          <dl className="grid gap-6 border-t border-cream/15 pt-8 sm:grid-cols-3">
            {STEPS.map((step) => (
              <div key={step.n} className="flex gap-3">
                <dt className="font-display text-2xl font-semibold text-sun">{step.n}</dt>
                <dd>
                  <p className="font-display text-base font-medium text-cream">{step.title}</p>
                  <p className="text-sm text-cream/70">{step.detail}</p>
                </dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
        <RegistrationForm />
      </main>
      <Footer />
    </div>
  );
}
