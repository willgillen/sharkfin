/**
 * Error handling utilities for API responses
 */

/**
 * Extract a user-friendly error message from an API error response.
 *
 * Handles:
 * - Pydantic validation errors (array of error objects)
 * - String error messages
 * - Fallback for unknown errors
 *
 * @param err - The error object from the API
 * @param fallbackMessage - Default message if no specific error is found
 * @returns A formatted error message string
 */
export function getErrorMessage(err: any, fallbackMessage: string = "An error occurred"): string {
  const detail = err?.response?.data?.detail;

  // Handle Pydantic validation errors (array of error objects)
  if (Array.isArray(detail)) {
    const errorMessages = detail
      .map((error: any) => {
        // Extract the field name from loc array (e.g., ["body", "notes"] -> "notes")
        const field = error.loc ? error.loc[error.loc.length - 1] : "";
        const msg = error.msg || "Invalid value";
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
    return errorMessages || fallbackMessage;
  }

  // Handle string error messages
  if (typeof detail === "string") {
    return detail;
  }

  // Fallback
  return fallbackMessage;
}
