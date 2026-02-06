"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { Input } from "@/components/ui";

export default function SetupAdminPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleContinue = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!fullName.trim()) {
      setError("Full name is required");
      return;
    }

    if (!email.trim()) {
      setError("Email is required");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Store in session storage for next steps
    sessionStorage.setItem("setup_admin", JSON.stringify({
      fullName,
      email,
      password
    }));

    router.push("/setup/categories");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
      <div className="max-w-md w-full space-y-8 p-8 bg-surface rounded-lg shadow-md">
        <div className="flex flex-col items-center">
          <Image
            src="/sharkfin_logo.png"
            alt="Shark Fin Logo"
            width={100}
            height={100}
            className="mb-4"
            priority
          />
          <h1 className="text-3xl font-bold text-center text-text-primary">
            Create Admin Account
          </h1>
          <p className="mt-2 text-center text-sm text-text-secondary">
            This will be your administrator account with full access
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleContinue}>
          {error && (
            <div className="rounded-md bg-danger-50 p-4">
              <p className="text-sm text-danger-800">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            <Input
              label="Full Name"
              id="fullName"
              name="fullName"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />

            <Input
              label="Email Address"
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
              autoComplete="new-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <Input
              label="Confirm Password"
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>

          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={() => router.push("/setup")}
              className="px-6 py-2 border border-border rounded-md text-text-secondary hover:bg-surface-secondary transition-colors"
            >
              ← Back
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-primary-600 text-text-inverse rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
            >
              Continue →
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
