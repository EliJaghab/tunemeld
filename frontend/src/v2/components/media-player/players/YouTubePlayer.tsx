import React, { useEffect, useState, useRef } from "react";
import clsx from "clsx";
import YouTube from "react-youtube";
import type { Track } from "@/types";

interface YouTubePlayerProps {
  track: Track;
  playing: boolean;
  onPlay: () => void;
  onPause: () => void;
}

export function YouTubePlayer({
  track,
  playing,
  onPlay,
  onPause,
}: YouTubePlayerProps): React.ReactElement | null {
  const [ytPlayer, setYtPlayer] = useState<any>(null);
  const [isReady, setIsReady] = useState(false);
  const currentTrackRef = useRef<string | null>(null);
  const playerRef = useRef<any>(null);

  const getYouTubeId = (url: string) => {
    try {
      const urlObj = new URL(url);
      return urlObj.searchParams.get("v");
    } catch (e) {
      return null;
    }
  };

  const url = track.youtubeUrl || "";
  const videoId = getYouTubeId(url);

  useEffect(() => {
    if (currentTrackRef.current !== track.isrc) {
      currentTrackRef.current = track.isrc;
      setIsReady(false);
      setYtPlayer(null);
      playerRef.current = null;
    }
  }, [track.isrc]);

  useEffect(() => {
    if (
      ytPlayer &&
      isReady &&
      playerRef.current === ytPlayer &&
      currentTrackRef.current === track.isrc
    ) {
      try {
        if (
          typeof ytPlayer.playVideo === "function" &&
          typeof ytPlayer.pauseVideo === "function"
        ) {
          if (playing) {
            ytPlayer.playVideo();
          } else {
            ytPlayer.pauseVideo();
          }
        }
      } catch (e) {
        if (
          !(
            e instanceof TypeError &&
            (e.message.includes("null") || e.message.includes("undefined"))
          )
        ) {
          console.error("[YouTubePlayer] Control error", e);
        }
      }
    }
  }, [playing, ytPlayer, isReady, track.isrc]);

  if (!videoId) return null;

  return (
    <div className={clsx("w-full mt-4 overflow-hidden rounded-2xl")}>
      <YouTube
        videoId={videoId}
        style={{ width: "100%", height: "200px" }}
        opts={{
          width: "100%",
          height: "200px",
          playerVars: {
            origin: window.location.origin,
            playsinline: 1,
            controls: 1,
          },
        }}
        onReady={(event) => {
          if (currentTrackRef.current === track.isrc) {
            const player = event.target;
            setYtPlayer(player);
            playerRef.current = player;
            setIsReady(true);
          }
        }}
        onStateChange={(event) => {
          if (event.data === 1) {
            onPlay();
          }
          if (event.data === 2) {
            onPause();
          }
        }}
        onError={(e) => console.error("[YouTubePlayer] Error", e)}
      />
    </div>
  );
}
