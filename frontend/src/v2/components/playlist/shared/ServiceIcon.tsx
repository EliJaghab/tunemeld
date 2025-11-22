import React from "react";
import clsx from "clsx";
import type { ServiceSource } from "@/types";

interface RankBadgeProps {
  rank: number;
  size?: "sm" | "md" | "lg";
}

function RankBadge({ rank, size = "lg" }: RankBadgeProps) {
  const isDoubleDigit = rank >= 10;

  const sizeConfig = {
    sm: {
      text: "text-[7px] desktop:text-[8px]",
      single: "w-[10px] h-[10px] desktop:w-[12px] desktop:h-[12px]",
      double:
        "min-w-[11px] w-[13px] h-[10px] desktop:min-w-[13px] desktop:w-[15px] desktop:h-[12px]",
      position: "-top-1 -right-1 desktop:-top-1 desktop:-right-1",
    },
    md: {
      text: "text-[8px] desktop:text-[9px]",
      single: "w-[12px] h-[12px] desktop:w-[14px] desktop:h-[14px]",
      double:
        "min-w-[13px] w-[15px] h-[12px] desktop:min-w-[15px] desktop:w-[17px] desktop:h-[14px]",
      position: "-top-1 -right-1 desktop:-top-1.5 desktop:-right-1.5",
    },
    lg: {
      text: "text-[9px] desktop:text-[11px]",
      single: "w-[14px] h-[14px] desktop:w-[18px] desktop:h-[18px]",
      double:
        "min-w-[14px] w-[18px] h-[14px] desktop:min-w-[18px] desktop:w-[22px] desktop:h-[18px] desktop:rounded-[11px]",
      position: "-top-1 -right-1 desktop:-top-[7px] desktop:-right-[7px]",
    },
  };

  const config = sizeConfig[size];

  return (
    <span
      className={clsx(
        "absolute",
        config.position,
        "flex items-center justify-center",
        "text-white font-bold",
        config.text,
        "leading-none",
        "z-50 rounded-full bg-badge-red",
        "shadow-[0_1px_3px_rgba(0,0,0,0.3)] px-0.5",
        isDoubleDigit ? config.double : config.single
      )}
    >
      {rank}
    </span>
  );
}

interface ServiceIconProps {
  source?: ServiceSource;
  rank?: number | null | undefined;
  size?: "sm" | "md" | "lg";
  badgeSize?: "sm" | "md" | "lg";
  onClick?: (e: React.MouseEvent) => void;
}

export function ServiceIcon({
  source,
  rank,
  size = "md",
  badgeSize,
  onClick,
}: ServiceIconProps) {
  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  const iconSizes = {
    sm: "w-4 h-4 desktop:w-5 desktop:h-5",
    md: "w-6 h-6 desktop:w-[30px] desktop:h-[30px]",
    lg: "w-8 h-8 desktop:w-10 desktop:h-10",
  };

  const effectiveBadgeSize = badgeSize || "lg";

  // If no source, just display the rank number (like RankBadge)
  if (!source) {
    return (
      <div
        className={clsx(
          sizeClasses[size],
          "text-black dark:text-white font-bold"
        )}
      >
        {rank}
      </div>
    );
  }

  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault();
      e.stopPropagation();
      onClick(e);
    }
  };

  return (
    <div className={clsx("relative inline-block")}>
      {onClick ? (
        <button
          onClick={handleClick}
          className={clsx("cursor-pointer")}
          aria-label={`${source.displayName}${rank ? ` - Rank ${rank}` : ""}`}
        >
          <img
            src={source.iconUrl}
            alt={source.displayName}
            className={clsx(iconSizes[size], "block")}
          />
        </button>
      ) : (
        <a
          href={source.url}
          target="_blank"
          rel="noreferrer"
          aria-label={`${source.displayName}${rank ? ` - Rank ${rank}` : ""}`}
        >
          <img
            src={source.iconUrl}
            alt={source.displayName}
            className={clsx(iconSizes[size], "block")}
          />
        </a>
      )}
      {rank !== null && rank !== undefined && (
        <RankBadge rank={rank} size={effectiveBadgeSize} />
      )}
    </div>
  );
}
