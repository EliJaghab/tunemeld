import React, { useEffect, useState } from "react";
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
    if (ytPlayer) {
      try {
        if (playing) {
          ytPlayer.playVideo();
        } else {
          ytPlayer.pauseVideo();
        }
      } catch (e) {
        console.error("[YouTubePlayer] Control error", e);
      }
    }
  }, [playing, ytPlayer]);

  if (!videoId) return null;

  return (
    <div className={clsx("w-full mt-4 overflow-hidden rounded-lg")}>
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
          setYtPlayer(event.target);
        }}
        onStateChange={(event) => {
          if (event.data === 1) onPlay();
          if (event.data === 2) onPause();
        }}
        onError={(e) => console.error("[YouTubePlayer] Error", e)}
      />
    </div>
  );
}
