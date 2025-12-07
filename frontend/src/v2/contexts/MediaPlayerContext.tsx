import React, {
  createContext,
  useContext,
  ReactNode,
  useState,
  useEffect,
  useLayoutEffect,
  useRef,
  useCallback,
  useMemo,
} from "react";
import { PLAYER, type PlayerValue } from "@/v2/constants";
import type { Track } from "@/types";

interface MediaPlayerContextValue {
  track: Track | null;
  activePlayer: PlayerValue | null;
  isOpen: boolean;
  isMinimized: boolean;
  isPlaying: boolean;
  hasInteracted: boolean;
  wasExplicitlyClosed: boolean;
  expand: () => void;
  collapse: () => void;
  togglePlay: () => void;
  setPlaying: (playing: boolean) => void;
  onClose: () => void;
  onServiceClick: (player: PlayerValue) => void;
}

const MediaPlayerContext = createContext<MediaPlayerContextValue | undefined>(
  undefined
);

interface MediaPlayerProviderProps {
  children: ReactNode;
  track: Track | null;
  activePlayer: PlayerValue | null;
  isOpen: boolean;
  hasInteracted: boolean;
  onClose: () => void;
  onServiceClick: (player: PlayerValue) => void;
  onPlayingStateChange: (isPlaying: boolean) => void;
}

export function MediaPlayerProvider({
  children,
  track,
  activePlayer,
  isOpen,
  hasInteracted,
  onClose,
  onServiceClick,
  onPlayingStateChange,
}: MediaPlayerProviderProps): React.ReactElement {
  const [isMinimizedState, setIsMinimizedState] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [lastSeenIsrc, setLastSeenIsrc] = useState<string | null>(null);
  const hasSeenOpenRef = useRef(false);
  const [wasExplicitlyClosed, setWasExplicitlyClosed] = useState(false);

  const currentIsrc = track?.isrc ?? null;
  const trackChanged = currentIsrc !== null && currentIsrc !== lastSeenIsrc;
  const isFirstOpen = isOpen && !hasSeenOpenRef.current;
  const isFirstTrack = currentIsrc !== null && lastSeenIsrc === null && isOpen;
  const shouldMinimize = trackChanged || isFirstOpen || isFirstTrack;

  const isMinimized = useMemo(() => {
    return shouldMinimize ? true : isMinimizedState;
  }, [shouldMinimize, isMinimizedState]);

  useLayoutEffect(() => {
    if (shouldMinimize) {
      setIsMinimizedState(true);
      setIsPlaying(false);
    }

    if (currentIsrc !== null) {
      setLastSeenIsrc(currentIsrc);
      // Reset explicit close flag when a new track opens
      setWasExplicitlyClosed(false);
    } else if (currentIsrc === null && lastSeenIsrc !== null) {
      setLastSeenIsrc(null);
    }

    if (isOpen) {
      hasSeenOpenRef.current = true;
    }
  }, [shouldMinimize, track?.isrc, isOpen, currentIsrc, lastSeenIsrc]);

  const isInitialMountRef = useRef(true);

  useEffect(() => {
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      return;
    }
    if (onPlayingStateChange) {
      onPlayingStateChange(isPlaying);
    }
  }, [isPlaying, onPlayingStateChange]);

  const expand = useCallback(() => {
    setIsMinimizedState(false);
  }, []);

  const collapse = useCallback(() => {
    setIsMinimizedState(true);
  }, []);

  const togglePlay = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const setPlaying = useCallback((playing: boolean) => {
    setIsPlaying(playing);
  }, []);

  const wrappedOnClose = useCallback(() => {
    setWasExplicitlyClosed(true);
    onClose();
  }, [onClose]);

  const value: MediaPlayerContextValue = {
    track,
    activePlayer,
    isOpen,
    isMinimized,
    isPlaying,
    hasInteracted,
    wasExplicitlyClosed,
    expand,
    collapse,
    togglePlay,
    setPlaying,
    onClose: wrappedOnClose,
    onServiceClick,
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
