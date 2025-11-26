/**
 * Format a play count number into an abbreviated string (e.g., 1.5M, 2.3K)
 */
export function formatAbbreviatedPlayCount(count: number): string {
  const abs = Math.abs(count);
  if (abs >= 1_000_000_000) {
    return `${(count / 1_000_000_000).toFixed(1)}B`;
  }
  if (abs >= 1_000_000) {
    return `${(count / 1_000_000).toFixed(1)}M`;
  }
  if (abs >= 1_000) {
    return `${(count / 1_000).toFixed(1)}K`;
  }
  return count.toLocaleString();
}

/**
 * Format a weekly change percentage into a string (e.g., +5.2%, -3.1%)
 */
export function formatWeeklyChangePercentage(percentage: number): string {
  const rounded = Math.round(percentage * 10) / 10;
  let formattedNumber = rounded.toFixed(1);
  if (formattedNumber.endsWith(".0")) {
    formattedNumber = formattedNumber.slice(0, -2);
  }
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${formattedNumber}%`;
}
