export function formatPlayCount(count: number | null | undefined): string {
  if (count === null || count === undefined || count === 0) {
    return "0";
  }

  if (count < 1000) {
    return String(count);
  }

  const suffixes: [number, string][] = [
    [1_000_000_000, "B"],
    [1_000_000, "M"],
    [1000, "k"],
  ];

  for (const [threshold, suffix] of suffixes) {
    if (count >= threshold) {
      const value = count / threshold;
      if (value >= 100) {
        return `${Math.round(value)}${suffix}`;
      } else if (value >= 10) {
        return `${value.toFixed(1)}${suffix}`;
      } else {
        return `${value.toFixed(2)}${suffix}`;
      }
    }
  }

  return String(count);
}

export function formatPercentageChange(
  percentage: number | null | undefined,
): string {
  if (percentage === null || percentage === undefined || percentage === 0.0) {
    return "0";
  }

  if (Math.abs(percentage) >= 100) {
    const formatted =
      percentage > 0
        ? `+${Math.round(percentage)}`
        : `${Math.round(percentage)}`;
    return formatted.substring(0, 4);
  } else if (Math.abs(percentage) >= 10) {
    return percentage > 0
      ? `+${Math.round(percentage)}`
      : `${Math.round(percentage)}`;
  } else if (Math.abs(percentage) >= 1) {
    return percentage > 0
      ? `+${percentage.toFixed(1)}`
      : `${percentage.toFixed(1)}`;
  } else {
    const sign = percentage > 0 ? "+" : "-";
    const decimalPart = Math.abs(percentage).toFixed(2).substring(2, 4);
    return `${sign}.${decimalPart}`;
  }
}
