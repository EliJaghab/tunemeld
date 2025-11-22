import React from "react";
import clsx from "clsx";
import { TrackCell } from "@/v2/components/playlist/shared/TrackCell";
import { SeenOn } from "@/v2/components/playlist/shared/SeenOn";
import type { Track } from "@/types";

interface TuneMeldRowProps {
  track: Track;
  displayRank: number;
  isLast?: boolean;
}

export function TuneMeldRow({
  track,
  displayRank,
  isLast = false,
}: TuneMeldRowProps) {
  return (
    <tr
      className={clsx(
        !isLast && "border-b border-gray-200 dark:border-gray-700",
        "hover:bg-gray-50 dark:hover:bg-gray-900",
        "transition-colors"
      )}
    >
      <TrackCell
        rank={displayRank}
        coverUrl={track.albumCoverUrl}
        trackName={track.trackName}
        artistName={track.artistName}
        isLast={isLast}
      />
      <td
        className={clsx(
          "desktop:table-cell py-2 px-3 min-w-[100px]",
          isLast && "rounded-br-[16px]"
        )}
      >
        <SeenOn track={track} />
      </td>
    </tr>
  );
}
