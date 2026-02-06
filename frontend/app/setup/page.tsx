"use client";

import { useRouter } from "next/navigation";
import Image from "next/image";

export default function SetupWelcomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
      <div className="max-w-2xl w-full space-y-8 p-8 bg-surface rounded-lg shadow-md">
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
            Welcome to Shark Fin
          </h1>
          <p className="mt-4 text-center text-xl text-text-secondary max-w-lg">
            Let's set up your personal finance tracker. This will only take a minute.
          </p>
        </div>

        <div className="bg-surface-secondary rounded-lg p-6 space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">
            What we'll set up:
          </h2>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-primary-600 mr-3">✓</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Admin Account:</strong> Create your administrator account with full access
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-primary-600 mr-3">✓</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Categories:</strong> Choose a preset or start with a clean slate
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-primary-600 mr-3">✓</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Sample Data (Optional):</strong> Add demo accounts and transactions to explore features
              </span>
            </li>
          </ul>
        </div>

        <div className="flex justify-center pt-4">
          <button
            onClick={() => router.push("/setup/admin")}
            className="px-8 py-3 bg-primary-600 text-text-inverse rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Get Started →
          </button>
        </div>
      </div>
    </div>
  );
}
