// Convert deployment status to emoji
export function getStatusEmoji(status: string): string {
  switch (status.toUpperCase()) {
    case "SUCCESS":
      return "✅";
    case "DEPLOYING":
    case "BUILDING":
    case "QUEUED":
      return "🔄";
    case "FAILED":
    case "ERROR":
      return "❌";
    case "REMOVED":
    case "CANCELED":
      return "🚫";
    default:
      return "❓";
  }
}
