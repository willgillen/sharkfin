/**
 * Setup wizard API client functions
 */
import apiClient from "./client";

export interface SetupStatus {
  setup_required: boolean;
  setup_completed: boolean;
}

export interface CategoryPreset {
  id: string;
  name: string;
  description: string;
  category_count: number;
}

export interface SetupRequest {
  email: string;
  password: string;
  full_name: string;
  create_default_categories: boolean;
  category_preset: string;
  create_sample_data: boolean;
}

export interface SetupResponse {
  success: boolean;
  message: string;
  user_id: number;
  categories_created: number;
  sample_data_created: boolean;
}

export const setupAPI = {
  /**
   * Check if setup is required (no users exist)
   */
  getStatus: async (): Promise<SetupStatus> => {
    const { data } = await apiClient.get<SetupStatus>("/v1/setup/status");
    return data;
  },

  /**
   * Get available category presets
   */
  getPresets: async (): Promise<CategoryPreset[]> => {
    const { data } = await apiClient.get<{ presets: CategoryPreset[] }>(
      "/v1/setup/presets"
    );
    return data.presets;
  },

  /**
   * Complete setup with user-provided data
   */
  completeSetup: async (setupData: SetupRequest): Promise<SetupResponse> => {
    const { data } = await apiClient.post<SetupResponse>(
      "/v1/setup/complete",
      setupData
    );
    return data;
  },
};
