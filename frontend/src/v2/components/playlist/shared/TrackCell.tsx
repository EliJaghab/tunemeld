import React from "react";
import clsx from "clsx";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";
import { MediaSquare } from "@/v2/components/shared/MediaSquare";

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
          "w-[60px] desktop:w-[80px]",
          "table-cell",
          isLast && "rounded-bl-[16px]"
        )}
      >
        <ServiceIcon rank={rank} />
      </td>
      <td
        className={clsx(
          "px-2 py-2 desktop:px-3 desktop:py-3",
          "w-[56px] desktop:w-[72px]",
          "table-cell"
        )}
      >
        {coverUrl && (
          <div
            className={clsx(
              "w-12 h-12 desktop:w-16 desktop:h-16",
              "flex-shrink-0"
            )}
          >
            <MediaSquare
              src={coverUrl}
              type="image"
              alt={`${trackName} cover`}
            />
          </div>
        )}
      </td>
      <td
        className={clsx(
          "px-3 py-2 desktop:px-4 desktop:py-3",
          "min-w-0",
          "table-cell"
        )}
      >
        <div className={clsx("flex flex-col")}>
          <div
            className={clsx(
              "font-semibold text-sm desktop:text-base",
              "text-black dark:text-white",
              "line-clamp-1"
            )}
            title={trackName}
          >
            {trackName}
          </div>
          <div
            className={clsx(
              "text-xs desktop:text-sm",
              "text-black dark:text-white",
              "line-clamp-1"
            )}
            title={artistName}
          >
            {artistName}
          </div>
        </div>
      </td>
    </>
  );
}
