"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/useAuth";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { importsAPI } from "@/lib/api";
import { ImportHistoryResponse } from "@/types";

export default function ImportHistoryPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [imports, setImports] = useState<ImportHistoryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [rollingBack, setRollingBack] = useState<number | null>(null);
  const [downloading, setDownloading] = useState<number | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    } else if (isAuthenticated) {
      fetchHistory();
    }
  }, [isAuthenticated, authLoading, router]);

  const fetchHistory = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await importsAPI.getHistory();
      setImports(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load import history");
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (importId: number) => {
    if (!confirm("Are you sure you want to rollback this import? All imported transactions will be deleted.")) {
      return;
    }

    setRollingBack(importId);
    setError("");

    try {
      await importsAPI.rollback(importId);
      // Refresh the list
      await fetchHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to rollback import");
    } finally {
      setRollingBack(null);
    }
  };

  const handleDownload = async (importId: number) => {
    setDownloading(importId);
    setError("");

    try {
      await importsAPI.downloadFile(importId);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to download file");
    } finally {
      setDownloading(null);
    }
  };

  const formatFileSize = (bytes: number | undefined) => {
    if (!bytes) return "-";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      completed: "bg-success-100 text-success-800",
      pending: "bg-warning-100 text-warning-800",
      failed: "bg-danger-100 text-danger-800",
      cancelled: "bg-surface-tertiary text-text-secondary",
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || "bg-surface-tertiary text-text-secondary"}`}>
        {status}
      </span>
    );
  };

  const getFileTypeIcon = (type: string) => {
    if (type === "csv") {
      return (
        <svg className="h-5 w-5 text-success-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className="h-5 w-5 text-primary-500" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
      </svg>
    );
  };

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-secondary">Loading...</p>
      </div>
    );
  }

  return (
    <DashboardLayout>
      <div className="px-4 sm:px-0 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-text-primary">Import History</h1>
            <p className="mt-2 text-sm text-text-secondary">
              View and manage all your transaction imports
            </p>
          </div>
          <button
            onClick={() => router.push("/dashboard/import")}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium hover:bg-primary-700"
          >
            New Import
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 rounded-md bg-danger-50 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-danger-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-danger-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-surface shadow rounded-lg p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-text-secondary">Loading import history...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && imports.length === 0 && (
          <div className="bg-surface shadow rounded-lg p-8 text-center">
            <svg className="mx-auto h-12 w-12 text-text-disabled" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-text-primary">No imports yet</h3>
            <p className="mt-1 text-sm text-text-tertiary">Get started by importing your first transaction file.</p>
            <div className="mt-6">
              <button
                onClick={() => router.push("/dashboard/import")}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                Import Transactions
              </button>
            </div>
          </div>
        )}

        {/* Import History Table */}
        {!loading && imports.length > 0 && (
          <div className="bg-surface shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-border">
              <thead className="bg-surface-secondary">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Account
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Results
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-text-tertiary uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-surface divide-y divide-border">
                {imports.map((importItem) => (
                  <tr key={importItem.id} className="hover:bg-surface-secondary">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getFileTypeIcon(importItem.import_type)}
                        <div className="ml-3">
                          <p className="text-sm font-medium text-text-primary">{importItem.filename}</p>
                          <p className="text-xs text-text-tertiary">
                            {importItem.import_type.toUpperCase()} · {formatFileSize(importItem.original_file_size)}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <p className="text-sm text-text-primary">{importItem.account_name || "Unknown"}</p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <p className="text-sm text-text-primary">{formatDate(importItem.started_at)}</p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm">
                        <p className="text-success-600 font-medium">{importItem.imported_count} imported</p>
                        {importItem.duplicate_count > 0 && (
                          <p className="text-warning-600">{importItem.duplicate_count} skipped</p>
                        )}
                        {importItem.error_count > 0 && (
                          <p className="text-danger-600">{importItem.error_count} errors</p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(importItem.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-3">
                        {importItem.has_file_data && (
                          <button
                            onClick={() => handleDownload(importItem.id)}
                            disabled={downloading === importItem.id}
                            className="text-primary-600 hover:text-primary-900 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Download original file"
                          >
                            {downloading === importItem.id ? (
                              "Downloading..."
                            ) : (
                              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                            )}
                          </button>
                        )}
                        {importItem.can_rollback && importItem.status === "completed" && (
                          <button
                            onClick={() => handleRollback(importItem.id)}
                            disabled={rollingBack === importItem.id}
                            className="text-danger-600 hover:text-danger-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {rollingBack === importItem.id ? "Rolling back..." : "Rollback"}
                          </button>
                        )}
                        {!importItem.has_file_data && !importItem.can_rollback && (
                          <span className="text-text-disabled">-</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary Stats */}
        {!loading && imports.length > 0 && (
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-3">
            <div className="bg-surface overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-text-disabled" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-text-tertiary truncate">Total Imports</dt>
                      <dd className="text-lg font-medium text-text-primary">{imports.length}</dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-surface overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-text-tertiary truncate">Total Imported</dt>
                      <dd className="text-lg font-medium text-text-primary">
                        {imports.reduce((sum, imp) => sum + imp.imported_count, 0)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-surface overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-warning-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-text-tertiary truncate">Duplicates Skipped</dt>
                      <dd className="text-lg font-medium text-text-primary">
                        {imports.reduce((sum, imp) => sum + imp.duplicate_count, 0)}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
