import React from "react";
import clsx from "clsx";
import { TuneMeldRow } from "@/v2/components/playlist/TuneMeldPlaylist/TuneMeldRow";
import { FilterButton } from "@/v2/components/shared/FilterButton";
import { GlassButton } from "@/v2/components/shared/GlassButton";
import { ResponsiveIcon } from "@/v2/components/shared/ResponsiveIcon";
import type { Track, Rank } from "@/types";

interface TuneMeldPlaylistTableProps {
  tracks: Track[];
  isCollapsed: boolean;
  onToggle: () => void;
  description?: string | null;
  ranks: Rank[];
  activeRank: string | null;
  onRankChange: (sortField: string) => void;
}

export function TuneMeldPlaylistTable({
  tracks,
  isCollapsed,
  onToggle,
  description,
  ranks,
  activeRank,
  onRankChange,
}: TuneMeldPlaylistTableProps) {
  return (
    <div className={clsx("overflow-x-auto")}>
      <div
        className={clsx(
          "px-4 py-3 desktop:px-6 desktop:py-4",
          !isCollapsed && "border-b-2 border-gray-300 dark:border-white"
        )}
      >
        <div className={clsx("flex items-start justify-between")}>
          <div className={clsx("flex-1")}>
            <h2
              className={clsx(
                "text-lg desktop:text-2xl font-bold",
                "text-black dark:text-white"
              )}
            >
              Tunemeld Playlist
              <span
                className={clsx(
                  "ml-2",
                  "text-sm desktop:text-base font-normal",
                  "text-gray-600 dark:text-gray-400"
                )}
              >
                ({tracks.length} tracks)
              </span>
            </h2>
            {description && (
              <p
                className={clsx(
                  "text-xs desktop:text-sm",
                  "text-black dark:text-white",
                  "mt-1"
                )}
              >
                {description}
              </p>
            )}
            {!isCollapsed && ranks.length > 0 && (
              <div className={clsx("flex flex-wrap gap-2 mt-3")}>
                {ranks.map((rank) => (
                  <FilterButton
                    key={rank.sortField}
                    onClick={() => onRankChange(rank.sortField)}
                    active={activeRank === rank.sortField}
                    text={rank.displayName}
                    ariaLabel={`Sort tracks by ${rank.displayName}`}
                  />
                ))}
              </div>
            )}
          </div>
          <GlassButton
            onClick={onToggle}
            className={clsx("flex-shrink-0 self-start", "rounded-full")}
            width={28}
            height={28}
            borderRadius={14}
            buttonClassName={clsx(
              "!p-0",
              "flex items-center justify-center",
              "w-full h-full",
              "rounded-full"
            )}
            ariaLabel={isCollapsed ? "Expand playlist" : "Collapse playlist"}
          >
            <ResponsiveIcon
              src={isCollapsed ? "./images/plus.svg" : "./images/minus.svg"}
              alt={isCollapsed ? "Expand" : "Collapse"}
              size="xs"
              className={clsx(
                "brightness-0 dark:brightness-0 dark:invert",
                "transition-opacity"
              )}
            />
          </GlassButton>
        </div>
      </div>

      {!isCollapsed && (
        <table className={clsx("w-full overflow-hidden rounded-b-[16px]")}>
          <tbody>
            {tracks.map((track, index) => (
              <TuneMeldRow
                key={track.isrc}
                track={track}
                displayRank={index + 1}
                isLast={index === tracks.length - 1}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
