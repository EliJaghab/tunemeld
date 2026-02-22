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

  // Render the rightmost cell content based on active rank
  const renderRightCellContent = () => {
    if (showServiceIcons) {
      return <SeenOn track={track} />;
    }

    if (showTotalPlays) {
      if (
        track.totalCurrentPlayCount == null ||
        isNaN(track.totalCurrentPlayCount)
      ) {
        return (
          <span
            className={clsx(
              "text-sm font-semibold text-gray-600 dark:text-gray-400"
            )}
          >
            —
          </span>
        );
      }
      const formatted = formatAbbreviatedPlayCount(track.totalCurrentPlayCount);
      return (
        <span
          className={clsx("text-sm font-semibold text-black dark:text-white")}
        >
          {formatted}
        </span>
      );
    }

    if (showTrending) {
      if (
        track.totalWeeklyChangePercentage == null ||
        isNaN(track.totalWeeklyChangePercentage)
      ) {
        return (
          <span
            className={clsx(
              "text-sm font-semibold text-black dark:text-gray-400"
            )}
          >
            —
          </span>
        );
      }
      const formatted = formatWeeklyChangePercentage(
        track.totalWeeklyChangePercentage
      );
      // Use same base classes as play count, then add color
      const baseClasses = "text-sm font-semibold text-black dark:text-white";
      const trendClass =
        track.totalWeeklyChangePercentage < 0
          ? "!text-red-700 dark:!text-red-400"
          : track.totalWeeklyChangePercentage > 0
            ? "!text-green-700 dark:!text-green-400"
            : "";
      return <span className={clsx(baseClasses, trendClass)}>{formatted}</span>;
    }

    return null;
  };

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
      <td
        className={clsx(
          "table-cell py-2 pl-3 pr-5",
          "w-[120px] desktop:w-[140px]",
          "text-sm font-semibold",
          isLast && "rounded-br-[16px]"
        )}
      >
        {renderRightCellContent()}
      </td>
    </tr>
  );
}
