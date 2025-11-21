import React from "react";
import type { ServiceSource } from "@/types";

interface RankBadgeProps {
  rank: number;
}

function RankBadge({ rank }: RankBadgeProps) {
  const isDoubleDigit = rank >= 10;
  return (
    <span
      className={`absolute -top-1 -right-1 desktop:-top-[7px] desktop:-right-[7px] flex items-center justify-center text-white font-bold text-[9px] desktop:text-[11px] leading-none z-10 rounded-full bg-badge-red shadow-[0_1px_3px_rgba(0,0,0,0.3)] px-0.5 ${
        isDoubleDigit
          ? "min-w-[14px] w-[18px] h-[14px] desktop:min-w-[18px] desktop:w-[22px] desktop:h-[18px] desktop:rounded-[11px]"
          : "w-[14px] h-[14px] desktop:w-[18px] desktop:h-[18px]"
      }`}
    >
      {rank}
    </span>
  );
}

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

  return (
    <div className="relative inline-block">
      <a
        href={source.url}
        target="_blank"
        rel="noreferrer"
        aria-label={`${source.displayName} - Rank ${rank}`}
      >
        <img
          src={source.iconUrl}
          alt={source.displayName}
          className="w-6 h-6 desktop:w-[30px] desktop:h-[30px]"
        />
      </a>
      {rank !== null && rank !== undefined && <RankBadge rank={rank} />}
    </div>
  );
}
