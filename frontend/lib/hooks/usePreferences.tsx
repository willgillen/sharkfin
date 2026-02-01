"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { usersAPI } from "@/lib/api/users";
import { UserPreferences, PreferencesMetadata } from "@/types";

interface UsePreferencesReturn {
  preferences: UserPreferences | null;
  metadata: PreferencesMetadata | null;
  loading: boolean;
  error: string | null;
  saving: Record<string, boolean>;
  updatePreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => Promise<void>;
  updatePreferences: (updates: Partial<UserPreferences>) => Promise<void>;
  resetPreference: (key: string) => Promise<void>;
  resetCategory: (category: string) => Promise<void>;
  resetAll: () => Promise<void>;
  refresh: () => Promise<void>;
  getDefaultValue: (key: string) => any;
  isModified: (key: string) => boolean;
}

export function usePreferences(): UsePreferencesReturn {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [metadata, setMetadata] = useState<PreferencesMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<Record<string, boolean>>({});

  // Track original values to detect modifications
  const originalValues = useRef<Record<string, any>>({});

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [prefs, meta] = await Promise.all([
        usersAPI.getPreferences(),
        usersAPI.getPreferencesMetadata(),
      ]);
      setPreferences(prefs);
      setMetadata(meta);

      // Store original values for modification detection
      originalValues.current = { ...prefs };
    } catch (err) {
      console.error("Failed to load preferences:", err);
      setError("Failed to load preferences. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const updatePreference = useCallback(
    async <K extends keyof UserPreferences>(key: K, value: UserPreferences[K]) => {
      setSaving((prev) => ({ ...prev, [key as string]: true }));
      try {
        const updatedPrefs = await usersAPI.updatePreferences({ [key]: value });
        setPreferences(updatedPrefs);
        setError(null);
      } catch (err) {
        console.error(`Failed to update preference ${String(key)}:`, err);
        setError(`Failed to save ${String(key)}. Please try again.`);
        throw err;
      } finally {
        setSaving((prev) => ({ ...prev, [key as string]: false }));
      }
    },
    []
  );

  const updatePreferences = useCallback(
    async (updates: Partial<UserPreferences>) => {
      const keys = Object.keys(updates);
      const savingState = keys.reduce((acc, key) => ({ ...acc, [key]: true }), {});
      setSaving((prev) => ({ ...prev, ...savingState }));

      try {
        const updatedPrefs = await usersAPI.updatePreferences(updates);
        setPreferences(updatedPrefs);
        setError(null);
      } catch (err) {
        console.error("Failed to update preferences:", err);
        setError("Failed to save preferences. Please try again.");
        throw err;
      } finally {
        const resetState = keys.reduce((acc, key) => ({ ...acc, [key]: false }), {});
        setSaving((prev) => ({ ...prev, ...resetState }));
      }
    },
    []
  );

  const resetPreference = useCallback(async (key: string) => {
    setSaving((prev) => ({ ...prev, [key]: true }));
    try {
      await usersAPI.resetPreference(key);
      // Reload to get updated values with defaults
      await loadData();
      setError(null);
    } catch (err) {
      console.error(`Failed to reset preference ${key}:`, err);
      setError(`Failed to reset ${key}. Please try again.`);
      throw err;
    } finally {
      setSaving((prev) => ({ ...prev, [key]: false }));
    }
  }, [loadData]);

  const resetCategory = useCallback(
    async (category: string) => {
      setSaving((prev) => ({ ...prev, [`category_${category}`]: true }));
      try {
        await usersAPI.resetCategoryPreferences(category);
        await loadData();
        setError(null);
      } catch (err) {
        console.error(`Failed to reset category ${category}:`, err);
        setError(`Failed to reset ${category} preferences. Please try again.`);
        throw err;
      } finally {
        setSaving((prev) => ({ ...prev, [`category_${category}`]: false }));
      }
    },
    [loadData]
  );

  const resetAll = useCallback(async () => {
    setSaving((prev) => ({ ...prev, all: true }));
    try {
      await usersAPI.resetAllPreferences();
      await loadData();
      setError(null);
    } catch (err) {
      console.error("Failed to reset all preferences:", err);
      setError("Failed to reset preferences. Please try again.");
      throw err;
    } finally {
      setSaving((prev) => ({ ...prev, all: false }));
    }
  }, [loadData]);

  const getDefaultValue = useCallback(
    (key: string): any => {
      if (!metadata?.preferences[key]) return undefined;
      return metadata.preferences[key].default;
    },
    [metadata]
  );

  const isModified = useCallback(
    (key: string): boolean => {
      if (!preferences || !metadata?.preferences[key]) return false;
      const defaultValue = metadata.preferences[key].default;
      const currentValue = preferences[key];
      return currentValue !== defaultValue;
    },
    [preferences, metadata]
  );

  return {
    preferences,
    metadata,
    loading,
    error,
    saving,
    updatePreference,
    updatePreferences,
    resetPreference,
    resetCategory,
    resetAll,
    refresh: loadData,
    getDefaultValue,
    isModified,
  };
}
