"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { setupAPI, CategoryPreset } from "@/lib/api/setup";

export default function SetupCategoriesPage() {
  const router = useRouter();
  const [selectedPreset, setSelectedPreset] = useState("standard");
  const [presets, setPresets] = useState<CategoryPreset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadPresets();
  }, []);

  const loadPresets = async () => {
    try {
      const presetsData = await setupAPI.getPresets();
      setPresets(presetsData);
      setLoading(false);
    } catch (err: any) {
      setError("Failed to load category presets");
      setLoading(false);
    }
  };

  const handleContinue = () => {
    // Store selection in session storage
    sessionStorage.setItem("setup_preset", selectedPreset);
    router.push("/setup/sample-data");
  };

  const handleBack = () => {
    router.push("/setup/admin");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-secondary">
        <p className="text-text-secondary">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-secondary py-12 px-4">
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
            Set Up Your Categories
          </h1>
          <p className="mt-2 text-center text-sm text-text-secondary">
            Choose a preset that fits your needs. You can always add or remove categories later.
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-danger-50 p-4">
            <p className="text-sm text-danger-800">{error}</p>
          </div>
        )}

        <div className="space-y-4">
          {presets.map((preset) => (
            <div
              key={preset.id}
              onClick={() => setSelectedPreset(preset.id)}
              className={`
                cursor-pointer p-4 rounded-lg border-2 transition-all
                ${
                  selectedPreset === preset.id
                    ? "border-primary-600 bg-primary-50"
                    : "border-border bg-surface hover:border-primary-300"
                }
              `}
            >
              <div className="flex items-start">
                <div className="flex-shrink-0 mt-1">
                  <div
                    className={`
                      w-5 h-5 rounded-full border-2 flex items-center justify-center
                      ${
                        selectedPreset === preset.id
                          ? "border-primary-600 bg-primary-600"
                          : "border-border bg-surface"
                      }
                    `}
                  >
                    {selectedPreset === preset.id && (
                      <div className="w-2 h-2 bg-white rounded-full" />
                    )}
                  </div>
                </div>
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-text-primary">
                      {preset.name}
                      {preset.id === "standard" && (
                        <span className="ml-2 text-sm font-normal text-primary-600">
                          (Recommended)
                        </span>
                      )}
                    </h3>
                    {preset.category_count > 0 && (
                      <span className="text-sm text-text-secondary">
                        {preset.category_count} categories
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-text-secondary">
                    {preset.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-between pt-4">
          <button
            type="button"
            onClick={handleBack}
            className="px-6 py-2 border border-border rounded-md text-text-secondary hover:bg-surface-secondary transition-colors"
          >
            ← Back
          </button>
          <button
            type="button"
            onClick={handleContinue}
            className="px-6 py-2 bg-primary-600 text-text-inverse rounded-md font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Continue →
          </button>
        </div>
      </div>
    </div>
  );
}
