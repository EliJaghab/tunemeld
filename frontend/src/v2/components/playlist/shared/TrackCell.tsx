import React from "react";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";

interface TrackCellProps {
  rank: number;
  coverUrl?: string | null | undefined;
  trackName: string;
  artistName: string;
}

export function TrackCell({
  rank,
  coverUrl,
  trackName,
  artistName,
}: TrackCellProps) {
  return (
    <>
      <td className="px-3 py-2 desktop:px-4 desktop:py-3">
        <ServiceIcon rank={rank} />
      </td>
      <td className="px-2 py-2 desktop:px-3 desktop:py-3">
        {coverUrl && (
          <img
            src={coverUrl}
            alt={`${trackName} cover`}
            className="w-12 h-12 desktop:w-16 desktop:h-16 rounded object-cover"
          />
        )}
      </td>
      <td className="px-3 py-2 desktop:px-4 desktop:py-3">
        <div className="flex flex-col">
          <div className="font-semibold text-sm desktop:text-base text-black dark:text-white line-clamp-1">
            {trackName}
          </div>
          <div className="text-xs desktop:text-sm text-black dark:text-white line-clamp-1">
            {artistName}
          </div>
        </div>
      </td>
    </>
  );
}
