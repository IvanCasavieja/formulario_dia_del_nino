import Image from "next/image";
import logo from "@/public/logo-tienda-inglesa.png";

export function Header() {
  return (
    <header className="bg-blue-deep">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <Image src={logo} alt="" width={36} height={36} priority />
          <div>
            <p className="font-display text-xs font-medium uppercase tracking-[0.3em] text-blue-light">
              Tienda Inglesa
            </p>
            <p className="font-display text-xl font-semibold text-white">Día del Niño</p>
          </div>
        </div>
      </div>
    </header>
  );
}
