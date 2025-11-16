import React from "react";
import type { ServiceSource } from "@/types";

interface ServiceIconProps {
  source?: ServiceSource;
  rank?: number | null | undefined;
  size?: "sm" | "md" | "lg";
}

export function ServiceIcon({ source, rank, size = "md" }: ServiceIconProps) {
  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  // If no source, just display the rank number (like RankBadge)
  if (!source) {
    return (
      <div
        className={`${sizeClasses[size]} text-black dark:text-white font-bold`}
      >
        {rank}
      </div>
    );
  }

  // If source exists, display service icon with rank badge
  const badgeClass =
    rank !== null && rank !== undefined && rank >= 10
      ? "rank-badge double-digit"
      : "rank-badge single-digit";

  return (
    <div className="source-icon-container relative inline-block">
      <a
        href={source.url}
        target="_blank"
        rel="noreferrer"
        aria-label={`${source.displayName} - Rank ${rank}`}
      >
        <img
          src={source.iconUrl}
          alt={source.displayName}
          className="source-icon h-5 w-5 desktop:h-6 desktop:w-6 rounded-full flex-shrink-0"
        />
      </a>
      {rank !== null && rank !== undefined && (
        <span className={badgeClass}>{rank}</span>
      )}
    </div>
  );
}
