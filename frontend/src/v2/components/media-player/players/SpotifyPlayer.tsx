import React, { useEffect, useState, useRef } from "react";
import clsx from "clsx";
import { PLAYER } from "@/v2/constants";
import { graphqlClient } from "@/services/graphql-client";
import type { Track } from "@/types";

interface SpotifyPlayerProps {
  track: Track;
}

export function SpotifyPlayer({
  track,
}: SpotifyPlayerProps): React.ReactElement | null {
  const [iframeSrc, setIframeSrc] = useState<string | null>(null);
  const currentTrackRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchIframe() {
      if (!track.spotifyUrl) return;

      if (track.isrc !== currentTrackRef.current) {
        setIframeSrc(null);
        currentTrackRef.current = track.isrc;

        try {
          const src = await graphqlClient.generateIframeUrl(
            PLAYER.SPOTIFY,
            track.spotifyUrl
          );
          if (!cancelled) {
            setIframeSrc(src);
          }
        } catch (error) {
          console.error("Failed to generate Spotify iframe URL:", error);
        }
      }
    }

    fetchIframe();

    return () => {
      cancelled = true;
    };
  }, [track]);

  if (!iframeSrc) {
    return (
      <div
        className={clsx(
          `w-full mt-4 overflow-hidden rounded-lg bg-black/5 dark:bg-white/5
          animate-pulse`
        )}
        style={{ height: "80px" }}
      />
    );
  }

  return (
    <div className={clsx("w-full mt-4 overflow-hidden rounded-lg")}>
      <iframe
        src={iframeSrc}
        className={clsx("w-full")}
        style={{
          height: "80px",
          border: "none",
        }}
        allow="autoplay; encrypted-media; picture-in-picture"
        allowFullScreen
        title="Spotify player"
      />
    </div>
  );
}
