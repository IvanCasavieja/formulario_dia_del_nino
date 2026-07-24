"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getJuradoToken } from "@/lib/juradoAuth";

// Client-side gate only, for UX (avoids flashing the voting screen before bouncing to
// login) - the real enforcement is the backend's require_jurado dependency on every
// /api/jurado/* route other than login, same principle as dashboard/layout.tsx.
export default function JuradoLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getJuradoToken()) {
      router.replace("/jurado-login");
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setReady(true);
  }, [router]);

  if (!ready) return null;

  return <div className="min-h-screen bg-zinc-50">{children}</div>;
}
