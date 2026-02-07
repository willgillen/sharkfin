import apiClient from "./client";
import { IconProviderStatus, LogoDevSettings, LogoDevSettingsUpdate } from "@/types";

export const settingsAPI = {
  async getIconProviders(): Promise<IconProviderStatus> {
    const { data } = await apiClient.get<IconProviderStatus>("/v1/settings/icon-providers");
    return data;
  },

  async getLogoDevSettings(): Promise<LogoDevSettings> {
    const { data } = await apiClient.get<LogoDevSettings>("/v1/settings/logo-dev");
    return data;
  },

  async updateLogoDevSettings(settings: LogoDevSettingsUpdate): Promise<LogoDevSettings> {
    const { data } = await apiClient.put<LogoDevSettings>("/v1/settings/logo-dev", settings);
    return data;
  },
};
