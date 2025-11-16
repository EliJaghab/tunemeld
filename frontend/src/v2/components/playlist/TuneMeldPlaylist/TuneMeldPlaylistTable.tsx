import React from "react";
import { TuneMeldRow } from "@/v2/components/playlist/TuneMeldPlaylist/TuneMeldRow";
import { FilterButton } from "@/v2/components/shared/FilterButton";
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
    <div className="overflow-x-auto">
      <div
        className={`px-4 py-3 desktop:px-6 desktop:py-4 ${
          !isCollapsed ? "border-b-2 border-gray-300 dark:border-gray-600" : ""
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h2 className="text-lg desktop:text-2xl font-bold text-black dark:text-white">
              TuneMeld Playlist
              <span className="ml-2 text-sm desktop:text-base font-normal text-gray-600 dark:text-gray-400">
                ({tracks.length} tracks)
              </span>
            </h2>
            {description && (
              <p className="text-xs desktop:text-sm text-black dark:text-white mt-1">
                {description}
              </p>
            )}
            {!isCollapsed && ranks.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
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
          <button
            onClick={onToggle}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-black/5 dark:hover:bg-white/5 transition-colors flex-shrink-0 self-start"
            aria-label={isCollapsed ? "Expand playlist" : "Collapse playlist"}
          >
            <span
              className="text-black dark:text-white text-sm transition-transform inline-block"
              style={{
                transform: isCollapsed ? "rotate(0deg)" : "rotate(180deg)",
              }}
            >
              ▼
            </span>
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <table className="w-full">
          <tbody>
            {tracks.map((track, index) => (
              <TuneMeldRow
                key={track.isrc}
                track={track}
                displayRank={index + 1}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
