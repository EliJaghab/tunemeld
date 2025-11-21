import React from "react";
import clsx from "clsx";
import { TrackCell } from "@/v2/components/playlist/shared/TrackCell";
import { SeenOn } from "@/v2/components/playlist/shared/SeenOn";
import type { Track } from "@/types";

interface TuneMeldRowProps {
  track: Track;
  displayRank: number;
}

export function TuneMeldRow({ track, displayRank }: TuneMeldRowProps) {
  return (
    <tr
      className={clsx(
        "border-b border-gray-200 dark:border-gray-700",
        "hover:bg-gray-50 dark:hover:bg-gray-800",
        "transition-colors"
      )}
    >
      <TrackCell
        rank={displayRank}
        coverUrl={track.albumCoverUrl}
        trackName={track.trackName}
        artistName={track.artistName}
      />
      <td className={clsx("desktop:table-cell py-2 px-3 min-w-[100px]")}>
        <SeenOn track={track} />
      </td>
    </tr>
  );
}
