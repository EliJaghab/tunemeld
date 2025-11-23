import React from "react";
import { PLAYER, type PlayerValue } from "@/v2/constants";
import type { Track } from "@/types";
import { YouTubePlayer } from "./YouTubePlayer";
import { SoundCloudPlayer } from "./SoundCloudPlayer";
import { SpotifyPlayer } from "./SpotifyPlayer";
import { AppleMusicPlayer } from "./AppleMusicPlayer";

interface ServicePlayerProps {
  track: Track;
  activePlayer: PlayerValue;
  playing: boolean;
  onPlay: () => void;
  onPause: () => void;
}

export function ServicePlayer({
  track,
  activePlayer,
  playing,
  onPlay,
  onPause,
}: ServicePlayerProps): React.ReactElement | null {
  switch (activePlayer) {
    case PLAYER.YOUTUBE:
      return (
        <YouTubePlayer
          track={track}
          playing={playing}
          onPlay={onPlay}
          onPause={onPause}
        />
      );
    case PLAYER.SOUNDCLOUD:
      return (
        <SoundCloudPlayer
          track={track}
          playing={playing}
          onPlay={onPlay}
          onPause={onPause}
        />
      );
    case PLAYER.SPOTIFY:
      return <SpotifyPlayer track={track} />;
    case PLAYER.APPLE_MUSIC:
      return <AppleMusicPlayer track={track} />;
    default:
      return null;
  }
}
