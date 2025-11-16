import React, { useState, useEffect } from "react";
import { TuneMeldPlaylistTable } from "@/v2/components/playlist/TuneMeldPlaylist/TuneMeldPlaylistTable";
import { PlaylistSkeleton } from "@/v2/components/playlist/shared/PlaylistSkeleton";
import { graphqlClient } from "@/services/graphql-client";
import type { Track } from "@/types";
import type { GenreValue } from "@/v2/constants";
import { RANKS } from "@/v2/constants";

interface TuneMeldPlaylistProps {
  genre: GenreValue;
}

export function TuneMeldPlaylist({ genre }: TuneMeldPlaylistProps) {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [description, setDescription] = useState<string | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeRank, setActiveRank] = useState<string | null>(() => {
    const defaultRank = RANKS.find((r) => r.isDefault);
    return defaultRank ? defaultRank.sortField : RANKS[0]?.sortField || null;
  });

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
        } else {
          setTracks([]);
        }

        const tuneMeldPlaylist = metadataData.playlists.find(
          (p) => p.serviceName === "tunemeld",
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
    <div className="flex justify-center px-3 desktop:px-4">
      <div className="w-full max-w-container">
        <div className="border-2 border-gray-500 dark:border-gray-600 rounded-media isolation-isolate">
          {loading ? (
            <div className="p-4 desktop:p-6">
              <PlaylistSkeleton rows={10} />
            </div>
          ) : tracks.length === 0 ? (
            <div className="p-4 desktop:p-6 text-center py-8 text-gray-600 dark:text-gray-400">
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
              onRankChange={setActiveRank}
            />
          )}
        </div>
      </div>
    </div>
  );
}
