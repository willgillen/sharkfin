import apiClient from "./client";
import {
  CSVPreviewResponse,
  OFXPreviewResponse,
  DuplicatesResponse,
  ImportExecuteResponse,
  ImportHistoryResponse,
  CSVColumnMapping,
  AnalyzeImportForRulesRequest,
  AnalyzeImportForRulesResponse,
} from "@/types";

export const importsAPI = {
  async previewCSV(file: File): Promise<CSVPreviewResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await apiClient.post<CSVPreviewResponse>(
      "/api/v1/imports/csv/preview",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    return data;
  },

  async previewOFX(file: File): Promise<OFXPreviewResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await apiClient.post<OFXPreviewResponse>(
      "/api/v1/imports/ofx/preview",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    return data;
  },

  async detectCSVDuplicates(
    file: File,
    accountId: number,
    columnMapping: CSVColumnMapping
  ): Promise<DuplicatesResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", accountId.toString());
    formData.append("column_mapping", JSON.stringify(columnMapping));

    const { data } = await apiClient.post<DuplicatesResponse>(
      "/api/v1/imports/csv/detect-duplicates",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    return data;
  },

  async detectOFXDuplicates(
    file: File,
    accountId: number
  ): Promise<DuplicatesResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", accountId.toString());

    const { data } = await apiClient.post<DuplicatesResponse>(
      "/api/v1/imports/ofx/detect-duplicates",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    return data;
  },

  async executeCSVImport(
    file: File,
    accountId: number,
    columnMapping: CSVColumnMapping,
    skipRows: number[]
  ): Promise<ImportExecuteResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", accountId.toString());
    formData.append("column_mapping", JSON.stringify(columnMapping));
    formData.append("skip_rows", JSON.stringify(skipRows));

    const { data } = await apiClient.post<ImportExecuteResponse>(
      "/api/v1/imports/csv/execute",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    return data;
  },

  async executeOFXImport(
    file: File,
    accountId: number,
    skipRows: number[]
  ): Promise<ImportExecuteResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("account_id", accountId.toString());
    formData.append("skip_rows", JSON.stringify(skipRows));

    const { data } = await apiClient.post<ImportExecuteResponse>(
      "/api/v1/imports/ofx/execute",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" }
      }
    );
    return data;
  },

  async getHistory(): Promise<ImportHistoryResponse[]> {
    const { data } = await apiClient.get<ImportHistoryResponse[]>(
      "/api/v1/imports/history"
    );
    return data;
  },

  async rollback(importId: number): Promise<void> {
    await apiClient.delete(`/api/v1/imports/history/${importId}`);
  },

  async analyzeForRules(request: AnalyzeImportForRulesRequest): Promise<AnalyzeImportForRulesResponse> {
    const { data } = await apiClient.post<AnalyzeImportForRulesResponse>(
      "/api/v1/imports/analyze-for-rules",
      request
    );
    return data;
  },

  async downloadFile(importId: number): Promise<void> {
    const response = await apiClient.get(`/api/v1/imports/${importId}/download`, {
      responseType: 'blob'
    });

    // Extract filename from Content-Disposition header
    const contentDisposition = response.headers['content-disposition'];
    let filename = `import-${importId}`;

    if (contentDisposition) {
      const matches = /filename="([^"]+)"/.exec(contentDisposition);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    // Create blob and download
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
};
