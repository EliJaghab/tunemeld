import React from "react";
import clsx from "clsx";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";

interface TrackCellProps {
  rank: number;
  coverUrl?: string | null | undefined;
  trackName: string;
  artistName: string;
  isLast?: boolean;
}

export function TrackCell({
  rank,
  coverUrl,
  trackName,
  artistName,
  isLast = false,
}: TrackCellProps) {
  return (
    <>
      <td
        className={clsx(
          "px-3 py-2 desktop:px-4 desktop:py-3",
          isLast && "rounded-bl-[16px]"
        )}
      >
        <ServiceIcon rank={rank} />
      </td>
      <td className={clsx("px-2 py-2 desktop:px-3 desktop:py-3")}>
        {coverUrl && (
          <img
            src={coverUrl}
            alt={`${trackName} cover`}
            className={clsx(
              "w-12 h-12 desktop:w-16 desktop:h-16",
              "rounded object-cover"
            )}
          />
        )}
      </td>
      <td className={clsx("px-3 py-2 desktop:px-4 desktop:py-3")}>
        <div className={clsx("flex flex-col")}>
          <div
            className={clsx(
              "font-semibold text-sm desktop:text-base",
              "text-black dark:text-white",
              "line-clamp-1"
            )}
          >
            {trackName}
          </div>
          <div
            className={clsx(
              "text-xs desktop:text-sm",
              "text-black dark:text-white",
              "line-clamp-1"
            )}
          >
            {artistName}
          </div>
        </div>
      </td>
    </>
  );
}
