export function Header() {
  return (
    <header className="bg-brand-deep">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <div>
          <p className="font-display text-xs font-medium uppercase tracking-[0.3em] text-sun">Tienda Inglesa</p>
          <p className="font-display text-xl font-semibold text-cream">Día del Niño</p>
        </div>
        <nav className="flex items-center gap-4 text-sm">
          <a
            href="#formulario"
            className="rounded-full bg-cream px-4 py-2 font-display text-sm font-medium text-brand-deep transition hover:bg-sun"
          >
            Participar
          </a>
        </nav>
      </div>
    </header>
  );
}
