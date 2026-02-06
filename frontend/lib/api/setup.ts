/**
 * Setup wizard API client functions
 */
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    const response = await axios.get<SetupStatus>(`${API_URL}/api/v1/setup/status`);
    return response.data;
  },

  /**
   * Get available category presets
   */
  getPresets: async (): Promise<CategoryPreset[]> => {
    const response = await axios.get<{ presets: CategoryPreset[] }>(
      `${API_URL}/api/v1/setup/presets`
    );
    return response.data.presets;
  },

  /**
   * Complete setup with user-provided data
   */
  completeSetup: async (setupData: SetupRequest): Promise<SetupResponse> => {
    const response = await axios.post<SetupResponse>(
      `${API_URL}/api/v1/setup/complete`,
      setupData
    );
    return response.data;
  },
};
