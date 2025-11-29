import React, { createContext, useContext, ReactNode } from "react";
import { PLAYER, type PlayerValue } from "@/v2/constants";
import type { Track } from "@/types";

interface MediaPlayerContextValue {
  track: Track | null;
  activePlayer: PlayerValue | null;
  isOpen: boolean;
  isInitialLoad: boolean;
  onClose: () => void;
  onServiceClick: (player: PlayerValue) => void;
  onPlayingStateChange: (isPlaying: boolean) => void;
}

const MediaPlayerContext = createContext<MediaPlayerContextValue | undefined>(
  undefined
);

interface MediaPlayerProviderProps {
  children: ReactNode;
  track: Track | null;
  activePlayer: PlayerValue | null;
  isOpen: boolean;
  isInitialLoad: boolean;
  onClose: () => void;
  onServiceClick: (player: PlayerValue) => void;
  onPlayingStateChange: (isPlaying: boolean) => void;
}

export function MediaPlayerProvider({
  children,
  track,
  activePlayer,
  isOpen,
  isInitialLoad,
  onClose,
  onServiceClick,
  onPlayingStateChange,
}: MediaPlayerProviderProps): React.ReactElement {
  const value: MediaPlayerContextValue = {
    track,
    activePlayer,
    isOpen,
    isInitialLoad,
    onClose,
    onServiceClick,
    onPlayingStateChange,
  };

  return (
    <MediaPlayerContext.Provider value={value}>
      {children}
    </MediaPlayerContext.Provider>
  );
}

export function useMediaPlayer(): MediaPlayerContextValue {
  const context = useContext(MediaPlayerContext);
  if (context === undefined) {
    throw new Error("useMediaPlayer must be used within a MediaPlayerProvider");
  }
  return context;
}
