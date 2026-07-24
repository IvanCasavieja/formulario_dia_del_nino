import type { Metadata } from "next";

// TEMP: the admin panel (app/admin/*, components/admin/*, lib/admin/*) is nested here
// so there's one working deployed link to it while the real, separate Vercel project
// for it (Root Directory `admin`, see the repo root README's "Frontends (Vercel)"
// section) isn't set up yet. admin/ itself is untouched and still fully deployable on
// its own - every file under here is a straight copy of the one in admin/, just with
// import paths and hrefs rewritten from / to /admin. Once the separate project exists,
// delete this whole app/admin (+ components/admin, lib/admin) tree.
export const metadata: Metadata = {
  title: "Panel de administración | Día del Niño - Tienda Inglesa",
  robots: { index: false, follow: false },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return children;
}
