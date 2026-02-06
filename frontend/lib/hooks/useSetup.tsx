"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { setupAPI, SetupStatus } from "../api/setup";

interface SetupContextType {
  setupRequired: boolean;
  loading: boolean;
  checkSetupStatus: () => Promise<void>;
}

const SetupContext = createContext<SetupContextType | undefined>(undefined);

export function SetupProvider({ children }: { children: ReactNode }) {
  const [setupRequired, setSetupRequired] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkSetupStatus = async () => {
    try {
      const status: SetupStatus = await setupAPI.getStatus();
      setSetupRequired(status.setup_required);
    } catch (error) {
      console.error("Failed to check setup status:", error);
      // On error, assume setup not required to avoid blocking
      setSetupRequired(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkSetupStatus();
  }, []);

  return (
    <SetupContext.Provider
      value={{
        setupRequired,
        loading,
        checkSetupStatus,
      }}
    >
      {children}
    </SetupContext.Provider>
  );
}

export function useSetup() {
  const context = useContext(SetupContext);
  if (context === undefined) {
    throw new Error("useSetup must be used within a SetupProvider");
  }
  return context;
}
