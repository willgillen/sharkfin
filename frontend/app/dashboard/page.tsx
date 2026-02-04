"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the new consolidated dashboard (formerly Reports)
    router.replace("/dashboard/reports");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
      <p className="text-text-secondary">Redirecting to dashboard...</p>
    </div>
  );
}
