"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/lib/hooks/useAuth";
import { useSetup } from "@/lib/hooks/useSetup";
import { Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { setupRequired, loading: setupLoading } = useSetup();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Redirect to setup if required
  useEffect(() => {
    if (!setupLoading && setupRequired) {
      router.push("/setup");
    }
  }, [setupRequired, setupLoading, router]);

  // Don't render if setup is required
  if (setupLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
        <p className="text-text-secondary">Loading...</p>
      </div>
    );
  }

  if (setupRequired) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login({ username: email, password });
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
      <div className="max-w-md w-full space-y-8 p-8 bg-surface rounded-lg shadow-md">
        <div className="flex flex-col items-center">
          <Image
            src="/sharkfin_logo.png"
            alt="Shark Fin Logo"
            width={140}
            height={140}
            className="mb-4"
            priority
          />
          <h1 className="text-4xl font-bold text-center text-text-primary">
            Shark Fin
          </h1>
          <h2 className="mt-4 text-center text-xl text-text-secondary">
            Sign in to your account
          </h2>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit} action="#">
          {error && (
            <div className="rounded-md bg-danger-50 p-4">
              <p className="text-sm text-danger-800">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <Input
              label="Email address"
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input
              label="Password"
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-text-inverse bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-text-secondary">
              Don't have an account?{" "}
              <Link href="/register" className="font-medium text-primary-600 hover:text-primary-500">
                Sign up
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
