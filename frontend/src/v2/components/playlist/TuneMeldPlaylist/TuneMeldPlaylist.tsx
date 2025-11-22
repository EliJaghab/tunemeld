import React, { useState, useEffect } from "react";
import clsx from "clsx";
import { TuneMeldPlaylistTable } from "@/v2/components/playlist/TuneMeldPlaylist/TuneMeldPlaylistTable";
import { PlaylistSkeleton } from "@/v2/components/playlist/shared/PlaylistSkeleton";
import { graphqlClient } from "@/services/graphql-client";
import type { Track } from "@/types";
import type { GenreValue } from "@/v2/constants";
import { RANKS } from "@/v2/constants";

interface TuneMeldPlaylistProps {
  genre: GenreValue;
  onTrackClick?: (track: Track) => void;
  onTracksLoaded?: (tracks: Track[]) => void;
  activeRank?: string;
  onRankChange?: (rank: string) => void;
}

export function TuneMeldPlaylist({
  genre,
  onTrackClick,
  onTracksLoaded,
  activeRank: activeRankProp,
  onRankChange: onRankChangeProp,
}: TuneMeldPlaylistProps) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [description, setDescription] = useState<string | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [internalActiveRank, setInternalActiveRank] = useState<string | null>(
    () => {
      const defaultRank = RANKS.find((r) => r.isDefault);
      return defaultRank ? defaultRank.sortField : RANKS[0]?.sortField || null;
    }
  );

  // Use prop if provided, otherwise use internal state
  const activeRank = activeRankProp || internalActiveRank;
  const handleRankChange = (rank: string) => {
    if (onRankChangeProp) {
      onRankChangeProp(rank);
    } else {
      setInternalActiveRank(rank);
    }
  };

  const handleToggle = () => {
    setIsCollapsed(!isCollapsed);
  };

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setLoading(true);
        const [playlistData, metadataData] = await Promise.all([
          graphqlClient.getPlaylist(genre, "tunemeld"),
          graphqlClient.getPlaylistMetadata(genre),
        ]);

        if (cancelled) return;

        if (playlistData && playlistData.tracks) {
          setTracks(playlistData.tracks);
          onTracksLoaded?.(playlistData.tracks);
        } else {
          setTracks([]);
          onTracksLoaded?.([]);
        }

        const tuneMeldPlaylist = metadataData.playlists.find(
          (p) => p.serviceName === "tunemeld"
        );
        if (tuneMeldPlaylist?.playlistCoverDescriptionText) {
          setDescription(tuneMeldPlaylist.playlistCoverDescriptionText);
        }
      } catch (error) {
        if (!cancelled) {
          console.error("Failed to fetch TuneMeld playlist:", error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [genre]);

  return (
    <div className={clsx("flex justify-center px-3 desktop:px-4")}>
      <div className={clsx("w-full max-w-container")}>
        <div
          className={clsx(
            "border-2 border-gray-300 dark:border-white",
            "rounded-media isolation-isolate"
          )}
        >
          {loading ? (
            <div className={clsx("p-4 desktop:p-6")}>
              <PlaylistSkeleton rows={10} />
            </div>
          ) : tracks.length === 0 ? (
            <div
              className={clsx(
                "p-4 desktop:p-6 text-center py-8",
                "text-gray-600 dark:text-gray-400"
              )}
            >
              No tracks found
            </div>
          ) : (
            <TuneMeldPlaylistTable
              tracks={tracks}
              isCollapsed={isCollapsed}
              onToggle={handleToggle}
              description={description}
              ranks={RANKS}
              activeRank={activeRank}
              onRankChange={handleRankChange}
              onTrackClick={onTrackClick}
            />
          )}
        </div>
      </div>
    </div>
  );
}
