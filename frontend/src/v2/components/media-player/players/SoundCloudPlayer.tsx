import React, { useEffect, useState, useRef } from "react";
import clsx from "clsx";
import { PLAYER } from "@/v2/constants";
import { graphqlClient } from "@/services/graphql-client";
import type { Track } from "@/types";

interface SoundCloudPlayerProps {
  track: Track;
  playing: boolean;
  onPlay: () => void;
  onPause: () => void;
}

export function SoundCloudPlayer({
  track,
  playing,
  onPlay,
  onPause,
}: SoundCloudPlayerProps): React.ReactElement | null {
  const [iframeSrc, setIframeSrc] = useState<string | null>(null);
  const currentTrackRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchIframe() {
      if (!track.soundcloudUrl) return;

      if (track.isrc !== currentTrackRef.current) {
        setIframeSrc(null);
        currentTrackRef.current = track.isrc;

        try {
          const src = await graphqlClient.generateIframeUrl(
            PLAYER.SOUNDCLOUD,
            track.soundcloudUrl
          );
          if (!cancelled) {
            setIframeSrc(src);
          }
        } catch (error) {
          console.error("Failed to generate SoundCloud iframe URL:", error);
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
          `w-full mt-4 overflow-hidden rounded-2xl bg-black/5 dark:bg-white/5
          animate-pulse`
        )}
        style={{ height: "166px" }}
      />
    );
  }

  return (
    <div className={clsx("w-full mt-4 overflow-hidden rounded-2xl")}>
      <iframe
        src={iframeSrc}
        className={clsx("w-full")}
        style={{
          height: "166px",
          border: "none",
        }}
        allow="autoplay; encrypted-media; picture-in-picture"
        allowFullScreen
        title="SoundCloud player"
      />
    </div>
  );
}
