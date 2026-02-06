"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import { useSetup } from "@/lib/hooks/useSetup";
import Link from "next/link";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();
  const { setupRequired, loading: setupLoading } = useSetup();

  useEffect(() => {
    // Check setup first - if setup is required, redirect to setup wizard
    if (!setupLoading && setupRequired) {
      router.push("/setup");
      return;
    }

    // If setup complete and user is authenticated, redirect to dashboard
    if (!loading && !setupLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, loading, setupRequired, setupLoading, router]);

  if (loading || setupLoading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-24">
        <p className="text-gray-600">Loading...</p>
      </main>
    );
  }

  // If setup is required, don't show this page (redirect happens in useEffect)
  if (setupRequired) {
    return null;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">🦈 Shark Fin</h1>
        <p className="text-xl text-gray-600 mb-8">
          Open-source Financial Planning & Budgeting
        </p>
        <div className="space-x-4">
          <Link
            href="/login"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Sign Up
          </Link>
        </div>
      </div>
    </main>
  );
}
