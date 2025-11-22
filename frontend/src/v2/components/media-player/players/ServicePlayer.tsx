import React, { useEffect, useState, useRef } from "react";
import clsx from "clsx";
import { PLAYER, type PlayerValue } from "@/v2/constants";
import { graphqlClient } from "@/services/graphql-client";
import type { Track } from "@/types";

interface ServicePlayerProps {
  track: Track;
  activePlayer: PlayerValue;
}

export function ServicePlayer({
  track,
  activePlayer,
}: ServicePlayerProps): React.ReactElement | null {
  const [iframeSrc, setIframeSrc] = useState<string | null>(null);
  const currentTrackRef = useRef<string | null>(null);
  const currentPlayerRef = useRef<PlayerValue | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchIframe() {
      if (
        track.isrc !== currentTrackRef.current ||
        activePlayer !== currentPlayerRef.current
      ) {
        setIframeSrc(null);
        currentTrackRef.current = track.isrc;
        currentPlayerRef.current = activePlayer;

        try {
          let url = "";
          if (activePlayer === PLAYER.YOUTUBE && track.youtubeUrl) {
            url = track.youtubeUrl;
          } else if (activePlayer === PLAYER.SPOTIFY && track.spotifyUrl) {
            url = track.spotifyUrl;
          } else if (
            activePlayer === PLAYER.APPLE_MUSIC &&
            track.appleMusicUrl
          ) {
            url = track.appleMusicUrl;
          } else if (
            activePlayer === PLAYER.SOUNDCLOUD &&
            track.soundcloudUrl
          ) {
            url = track.soundcloudUrl;
          }

          if (url) {
            const src = await graphqlClient.generateIframeUrl(
              activePlayer,
              url
            );
            if (!cancelled) {
              setIframeSrc(src);
            }
          }
        } catch (error) {
          console.error("Failed to generate iframe URL:", error);
        }
      }
    }

    fetchIframe();

    return () => {
      cancelled = true;
    };
  }, [track, activePlayer]);

  if (!iframeSrc) return null;

  const getHeight = () => {
    switch (activePlayer) {
      case PLAYER.YOUTUBE:
        return "200px";
      case PLAYER.SOUNDCLOUD:
        return "166px";
      case PLAYER.APPLE_MUSIC:
        return "175px";
      default:
        return "80px";
    }
  };

  return (
    <div className={clsx("w-full mt-4 overflow-hidden rounded-lg")}>
      <iframe
        src={iframeSrc}
        className={clsx("w-full")}
        style={{
          height: getHeight(),
          border: "none",
        }}
        allow="autoplay; encrypted-media; picture-in-picture"
        allowFullScreen
        title={`${activePlayer} player`}
      />
    </div>
  );
}
