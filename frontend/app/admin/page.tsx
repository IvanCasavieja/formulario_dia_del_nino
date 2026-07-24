// TEMP copy of admin/app/page.tsx - see app/admin/layout.tsx.

import { redirect } from "next/navigation";

export default function AdminIndexPage() {
  redirect("/admin/dashboard");
}
