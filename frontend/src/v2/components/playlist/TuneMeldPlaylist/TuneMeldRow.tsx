import React from "react";
import clsx from "clsx";
import { TrackCell } from "@/v2/components/playlist/shared/TrackCell";
import { SeenOn } from "@/v2/components/playlist/shared/SeenOn";
import {
  formatAbbreviatedPlayCount,
  formatWeeklyChangePercentage,
} from "@/v2/utils/formatPlayCount";
import { RANK } from "@/v2/constants";
import type { Track } from "@/types";

interface TuneMeldRowProps {
  track: Track;
  displayRank: number;
  isLast?: boolean;
  activeRank?: string | null;
  onTrackClick?: (track: Track) => void;
}

function PlayCountCell({
  playCount,
}: {
  playCount: number | null | undefined;
}): React.ReactElement | null {
  if (playCount == null || isNaN(playCount)) {
    return (
      <td
        className={clsx(
          "desktop:table-cell py-2 px-3",
          "text-sm font-semibold",
          "min-w-[80px]"
        )}
      >
        <span className={clsx("text-gray-400 dark:text-gray-500")}>—</span>
      </td>
    );
  }

  const formatted = formatAbbreviatedPlayCount(playCount);

  return (
    <td
      className={clsx(
        "desktop:table-cell py-2 px-3",
        "text-sm font-semibold",
        "min-w-[80px]"
      )}
    >
      <span className={clsx("text-black dark:text-white")}>{formatted}</span>
    </td>
  );
}

function TrendingCell({
  percentage,
}: {
  percentage: number | null | undefined;
}): React.ReactElement | null {
  if (percentage == null || isNaN(percentage)) {
    return (
      <td
        className={clsx(
          "desktop:table-cell py-2 px-3",
          "text-sm font-semibold",
          "min-w-[80px]"
        )}
      >
        <span className={clsx("text-gray-400 dark:text-gray-500")}>—</span>
      </td>
    );
  }

  const formatted = formatWeeklyChangePercentage(percentage);
  const trendClass =
    percentage < 0
      ? "text-red-600 dark:text-red-400"
      : percentage > 0
        ? "text-green-600 dark:text-green-400"
        : "text-gray-700 dark:text-gray-300";

  return (
    <td
      className={clsx(
        "desktop:table-cell py-2 px-3",
        "text-sm font-semibold",
        "min-w-[80px]"
      )}
    >
      <span className={clsx(trendClass)}>{formatted}</span>
    </td>
  );
}

export function TuneMeldRow({
  track,
  displayRank,
  isLast = false,
  activeRank,
  onTrackClick,
}: TuneMeldRowProps) {
  const handleClick = () => {
    if (onTrackClick) {
      onTrackClick(track);
    }
  };

  const showTotalPlays = activeRank === RANK.TOTAL_PLAYS;
  const showTrending = activeRank === RANK.TRENDING;
  const showServiceIcons = !activeRank || activeRank === RANK.TUNEMELD_RANK;

  return (
    <tr
      onClick={handleClick}
      className={clsx(
        !isLast && "border-b border-gray-200 dark:border-gray-700",
        "hover:bg-gray-50 dark:hover:bg-gray-900",
        "transition-colors",
        onTrackClick && "cursor-pointer"
      )}
    >
      <TrackCell
        rank={displayRank}
        coverUrl={track.albumCoverUrl}
        trackName={track.trackName}
        artistName={track.artistName}
        isLast={isLast}
      />
      {showTotalPlays && (
        <PlayCountCell playCount={track.totalCurrentPlayCount} />
      )}
      {showTrending && (
        <TrendingCell percentage={track.totalWeeklyChangePercentage} />
      )}
      {showServiceIcons && (
        <td
          className={clsx(
            "desktop:table-cell py-2 px-3 min-w-[100px]",
            isLast && "rounded-br-[16px]"
          )}
        >
          <SeenOn track={track} />
        </td>
      )}
    </tr>
  );
}
