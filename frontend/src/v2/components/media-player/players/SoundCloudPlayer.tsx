import React from "react";
import clsx from "clsx";
import ReactPlayer from "react-player";
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
  const url = track.soundcloudUrl || "";

  if (!url) return null;

  return (
    <div className={clsx("w-full mt-4 overflow-hidden rounded-lg")}>
      <ReactPlayer
        url={url}
        playing={playing}
        onPlay={onPlay}
        onPause={onPause}
        width="100%"
        height="166px"
        controls
        config={{
          soundcloud: {
            options: { show_artwork: true, visual: true },
          },
        }}
      />
    </div>
  );
}
