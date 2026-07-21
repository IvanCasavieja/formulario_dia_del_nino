import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { RegistrationForm } from "@/components/RegistrationForm/RegistrationForm";

export default function Home() {
  return (
    <div className="min-h-screen bg-bg text-ink">
      <Header />

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
        <RegistrationForm />
      </main>
      <Footer />
    </div>
  );
}
