export function formatCurrency(amount: string | number, currency: string = "USD"): string {
  const numAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency,
  }).format(numAmount);
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

export function formatPercentage(value: string | number): string {
  const numValue = typeof value === "string" ? parseFloat(value) : value;
  return `${numValue.toFixed(1)}%`;
}

/**
 * Format a month string (YYYY-MM) for display, avoiding timezone issues.
 * Using UTC parsing prevents dates like "2025-01-01" from shifting to Dec 31 2024 in local time.
 */
export function formatMonthYear(
  monthString: string,
  options: { month?: "short" | "long"; year?: "2-digit" | "numeric" } = {}
): string {
  const { month = "short", year = "2-digit" } = options;
  const [yearNum, monthNum] = monthString.split("-").map(Number);
  const displayDate = new Date(Date.UTC(yearNum, monthNum - 1, 15));
  return displayDate.toLocaleDateString("en-US", {
    month,
    year,
    timeZone: "UTC",
  });
}
