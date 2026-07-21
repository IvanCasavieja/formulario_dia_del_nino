"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getAdminToken } from "@/lib/adminAuth";

// Client-side gate only, for UX (avoids flashing the dashboard before bouncing to
// login) - the real enforcement is the backend's require_admin dependency on every
// /api/admin/* route, which checks the JWT regardless of what this layout does.
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getAdminToken()) {
      router.replace("/login");
      return;
    }
    // sessionStorage only exists client-side, so this has to run post-mount rather
    // than during render (matching server/first-hydration output, then correcting) -
    // exactly the "sync with an external system" case the lint rule's own docs carve
    // out as legitimate, not the "should've computed this during render" case.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setReady(true);
  }, [router]);

  if (!ready) return null;

  return <div className="min-h-screen bg-zinc-50">{children}</div>;
}
