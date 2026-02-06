"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { setupAPI } from "@/lib/api/setup";
import { useAuth } from "@/lib/hooks/useAuth";

export default function SetupSampleDataPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [createSampleData, setCreateSampleData] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleComplete = async () => {
    setError("");
    setLoading(true);

    try {
      // Retrieve admin data from session storage
      const adminDataStr = sessionStorage.getItem("setup_admin");
      const preset = sessionStorage.getItem("setup_preset") || "standard";

      if (!adminDataStr) {
        setError("Setup data not found. Please start over.");
        setLoading(false);
        return;
      }

      const adminData = JSON.parse(adminDataStr);

      // Complete setup
      const response = await setupAPI.completeSetup({
        email: adminData.email,
        password: adminData.password,
        full_name: adminData.fullName,
        create_default_categories: preset !== "empty",
        category_preset: preset,
        create_sample_data: createSampleData,
      });

      // Clear session storage
      sessionStorage.removeItem("setup_admin");
      sessionStorage.removeItem("setup_preset");

      // Log in the user
      await login({
        username: adminData.email,
        password: adminData.password,
      });

      // Redirect to completion page
      router.push("/setup/complete");
    } catch (err: any) {
      console.error("Setup error:", err);
      setError(err.response?.data?.detail || "Setup failed. Please try again.");
      setLoading(false);
    }
  };

  const handleBack = () => {
    router.push("/setup/categories");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
      <div className="max-w-2xl w-full space-y-8 p-8 bg-surface rounded-lg shadow-md">
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
            Sample Data (Optional)
          </h1>
          <p className="mt-2 text-center text-sm text-text-secondary max-w-lg">
            Would you like to create sample data to explore how Shark Fin works?
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-danger-50 p-4">
            <p className="text-sm text-danger-800">{error}</p>
          </div>
        )}

        <div className="bg-surface-secondary rounded-lg p-6">
          <label className="flex items-start cursor-pointer">
            <input
              type="checkbox"
              checked={createSampleData}
              onChange={(e) => setCreateSampleData(e.target.checked)}
              className="mt-1 h-5 w-5 text-primary-600 border-border rounded focus:ring-primary-500"
            />
            <div className="ml-3">
              <span className="text-base font-medium text-text-primary">
                Create sample accounts and transactions
              </span>
              <p className="mt-1 text-sm text-text-secondary">
                Includes checking, savings, and credit card accounts with realistic
                transactions from the past month. You can delete this data later.
              </p>
              <div className="mt-3 space-y-1 text-sm text-text-secondary">
                <p>• 3 accounts (checking, savings, credit card)</p>
                <p>• 20+ sample transactions</p>
                <p>• Various categories and payees</p>
              </div>
            </div>
          </label>
        </div>

        <div className="flex justify-between pt-4">
          <button
            type="button"
            onClick={handleBack}
            disabled={loading}
            className="px-6 py-2 border border-border rounded-md text-text-secondary hover:bg-surface-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Back
          </button>
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading}
            className="px-6 py-2 bg-primary-600 text-text-inverse rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Setting up..." : "Complete Setup →"}
          </button>
        </div>
      </div>
    </div>
  );
}
