"use client";

import { useRouter } from "next/navigation";
import Image from "next/image";

export default function SetupCompletePage() {
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
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-4xl font-bold text-center text-text-primary">
            Setup Complete!
          </h1>
          <p className="mt-4 text-center text-xl text-text-secondary max-w-lg">
            Your Shark Fin instance is ready to use.
          </p>
        </div>

        <div className="bg-surface-secondary rounded-lg p-6 space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">
            Next steps:
          </h2>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="text-primary-600 mr-3 text-xl">1.</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Add your financial accounts:</strong> Create accounts for your checking, savings, credit cards, and investments
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-primary-600 mr-3 text-xl">2.</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Import transactions:</strong> Upload CSV, OFX, or QFX files from your bank
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-primary-600 mr-3 text-xl">3.</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Set up budgets:</strong> Create budgets for your spending categories to track your goals
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-primary-600 mr-3 text-xl">4.</span>
              <span className="text-text-secondary">
                <strong className="text-text-primary">Explore reports:</strong> View insights into your spending patterns and financial health
              </span>
            </li>
          </ul>
        </div>

        <div className="flex justify-center pt-4">
          <button
            onClick={() => router.push("/dashboard")}
            className="px-8 py-3 bg-primary-600 text-text-inverse rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Go to Dashboard →
          </button>
        </div>
      </div>
    </div>
  );
}
