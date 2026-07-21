import Image from "next/image";
import icon from "@/public/logo-tienda-inglesa.png";
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

      <section className="relative overflow-hidden bg-blue-deep">
        <div
          aria-hidden
          className="animate-float-soft pointer-events-none absolute -top-16 -right-16 h-[26rem] w-[26rem] opacity-[0.08] sm:h-[32rem] sm:w-[32rem]"
        >
          <Image src={icon} alt="" fill className="object-contain" />
        </div>

        <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-10 px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="max-w-3xl space-y-5">
            <p className="font-display text-sm font-medium tracking-[0.3em] text-blue-light uppercase">Sorteo Día del Niño</p>
            <h1 className="text-balance font-display text-4xl leading-[1.05] font-semibold text-white sm:text-5xl lg:text-6xl">
              Contanos por qué tu hijo o hija se merece ganar.
            </h1>
            <p className="max-w-xl text-lg text-white/80">
              Grabá un video cortito, completá el formulario y quedá participando del sorteo de Tienda Inglesa por el Día del Niño.
            </p>
          </div>

          <a
            href="#formulario"
            className="inline-flex w-fit items-center gap-2 rounded-full bg-red px-7 py-3.5 font-display font-medium text-white shadow-lg shadow-black/20 transition hover:-translate-y-0.5 hover:bg-red-deep"
          >
            Quiero participar
          </a>

          <dl className="grid gap-6 border-t border-white/15 pt-8 sm:grid-cols-3">
            {STEPS.map((step) => (
              <div key={step.n} className="flex gap-3">
                <dt className="font-display text-2xl font-semibold text-blue-light">{step.n}</dt>
                <dd>
                  <p className="font-display text-base font-medium text-white">{step.title}</p>
                  <p className="text-sm text-white/70">{step.detail}</p>
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
