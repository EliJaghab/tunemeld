import React from "react";
import clsx from "clsx";

interface PlaylistSkeletonProps {
  rows?: number;
}

export function PlaylistSkeleton({ rows = 10 }: PlaylistSkeletonProps) {
  return (
    <div className={clsx("space-y-2")}>
      {Array.from({
        length: rows,
      }).map((_, index) => (
        <div key={index} className={clsx("flex items-center gap-3 py-2")}>
          <div
            className={clsx(
              "w-8 h-8 bg-black/10 dark:bg-white/10 rounded-full",
              "animate-pulse"
            )}
          />
          <div
            className={clsx(
              "w-12 h-12 desktop:w-16 desktop:h-16",
              "bg-black/10 dark:bg-white/10 rounded",
              "animate-pulse"
            )}
          />
          <div className={clsx("flex-1 space-y-2")}>
            <div
              className={clsx(
                "h-4 bg-black/10 dark:bg-white/10 rounded w-3/4",
                "animate-pulse"
              )}
            />
            <div
              className={clsx(
                "h-3 bg-black/10 dark:bg-white/10 rounded w-1/2",
                "animate-pulse"
              )}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
