import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { VoteForm } from "@/components/VoteForm/VoteForm";

export default function VotarPage() {
  return (
    <div className="min-h-screen bg-bg text-ink">
      <Header />

      <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-4 py-14 sm:px-6 lg:px-8 lg:py-20">
        <VoteForm />
      </main>
      <Footer />
    </div>
  );
}
