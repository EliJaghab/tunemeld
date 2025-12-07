import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import {
  GENRE,
  RANKS,
  RANK,
  PLAYER,
  type GenreValue,
  type PlayerValue,
} from "@/v2/constants";
import type { Track } from "@/types";

interface UseAppRoutingReturn {
  genre: GenreValue;
  rank: string;
  isrc: string | null;
  player: PlayerValue | null;
  selectedTrack: Track | null;
  isMediaPlayerOpen: boolean;
  hasInteracted: boolean;
  setGenre: (genre: GenreValue) => void;
  setRank: (rank: string) => void;
  openTrack: (track: Track) => void;
  closeMediaPlayer: () => void;
  setPlayer: (player: PlayerValue) => void;
  onPlayingStateChange: (isPlaying: boolean) => void;
}

export function useAppRouting(playlistTracks: Track[]): UseAppRoutingReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [activePlayer, setActivePlayer] = useState<PlayerValue | null>(null);
  const [isMediaPlayerOpen, setIsMediaPlayerOpen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);
  const lastGenreRef = useRef<GenreValue | null>(null);
  const hasTracksLoadedRef = useRef(false);

  const genreParam = searchParams.get("genre");
  const genre: GenreValue = useMemo(() => {
    const validGenre =
      genreParam && Object.values(GENRE).includes(genreParam as GenreValue)
        ? (genreParam as GenreValue)
        : GENRE.POP;
    return validGenre;
  }, [genreParam]);

  // Set default genre in URL if missing
  useEffect(() => {
    if (!genreParam || genreParam !== genre) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("genre", genre);
      setSearchParams(newParams, { replace: true });
    }
  }, [genreParam, genre, searchParams, setSearchParams]);

  const rank =
    searchParams.get("rank") ||
    RANKS.find((r) => r.isDefault)?.sortField ||
    RANK.TUNEMELD_RANK;

  const isrc = searchParams.get("isrc");

  useEffect(() => {
    const playerParam = searchParams.get("player");
    const isrcParam = searchParams.get("isrc");

    if (
      playerParam &&
      Object.values(PLAYER).includes(playerParam as PlayerValue)
    ) {
      setActivePlayer(playerParam as PlayerValue);
    } else if (!playerParam && isrcParam) {
      setActivePlayer(null);
    }
  }, [searchParams]);

  const getDefaultPlayer = useCallback((track: Track): PlayerValue | null => {
    if (track.youtubeSource) return PLAYER.YOUTUBE;
    if (track.spotifySource) return PLAYER.SPOTIFY;
    if (track.appleMusicSource) return PLAYER.APPLE_MUSIC;
    if (track.soundcloudSource) return PLAYER.SOUNDCLOUD;
    return null;
  }, []);

  const openFirstTrack = useCallback(
    (tracks: Track[], forGenre: GenreValue) => {
      if (tracks.length === 0) return;

      const firstTrack = tracks[0];
      const defaultPlayer = getDefaultPlayer(firstTrack);
      const newParams = new URLSearchParams(searchParams);
      newParams.set("genre", forGenre);
      newParams.set("rank", rank);
      newParams.set("isrc", firstTrack.isrc);
      if (defaultPlayer) {
        newParams.set("player", defaultPlayer);
      }

      setSearchParams(newParams, { replace: true });
      setSelectedTrack(firstTrack);
      setIsMediaPlayerOpen(true);
    },
    [searchParams, rank, setSearchParams, getDefaultPlayer]
  );

  // Track genre changes and handle auto-loading
  useEffect(() => {
    const genreChanged =
      lastGenreRef.current !== null && lastGenreRef.current !== genre;

    if (genreChanged) {
      hasTracksLoadedRef.current = false;
      setHasInteracted(false);
    }
    lastGenreRef.current = genre;

    if (playlistTracks.length === 0) {
      return;
    }

    const tracksJustLoaded =
      !hasTracksLoadedRef.current && playlistTracks.length > 0;
    if (tracksJustLoaded) {
      hasTracksLoadedRef.current = true;
    }

    if (isrc) {
      const track = playlistTracks.find((t) => t.isrc === isrc);
      if (track) {
        if (selectedTrack?.isrc !== track.isrc || !isMediaPlayerOpen) {
          setSelectedTrack(track);
          setIsMediaPlayerOpen(true);
        }
      } else {
        if (!hasInteracted && !isPlaying) {
          openFirstTrack(playlistTracks, genre);
        }
      }
      return;
    }

    if (!hasInteracted && !isPlaying && (genreChanged || tracksJustLoaded)) {
      openFirstTrack(playlistTracks, genre);
    }
  }, [
    genre,
    isrc,
    playlistTracks,
    isPlaying,
    selectedTrack,
    isMediaPlayerOpen,
    hasInteracted,
    openFirstTrack,
  ]);

  const setGenre = useCallback(
    (newGenre: GenreValue) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("genre", newGenre);

      if (hasInteracted && selectedTrack) {
        newParams.set("isrc", selectedTrack.isrc);
        if (activePlayer) {
          newParams.set("player", activePlayer);
        }
      } else {
        newParams.delete("isrc");
        newParams.delete("player");
      }

      setSearchParams(newParams, { replace: false });
    },
    [searchParams, setSearchParams, selectedTrack, activePlayer, hasInteracted]
  );

  const setRank = useCallback(
    (newRank: string) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("rank", newRank);
      if (isrc) {
        newParams.set("isrc", isrc);
      }
      if (activePlayer) {
        newParams.set("player", activePlayer);
      }
      setSearchParams(newParams, { replace: false });
    },
    [searchParams, isrc, activePlayer, setSearchParams]
  );

  const closeMediaPlayer = useCallback(() => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("isrc");
    newParams.delete("player");
    setSearchParams(newParams, { replace: true });
    setSelectedTrack(null);
    setIsMediaPlayerOpen(false);
  }, [searchParams, setSearchParams]);

  const setPlayer = useCallback(
    (newPlayer: PlayerValue) => {
      if (selectedTrack) {
        const newParams = new URLSearchParams(searchParams);
        newParams.set("genre", genre);
        newParams.set("rank", rank);
        newParams.set("isrc", selectedTrack.isrc);
        newParams.set("player", newPlayer);
        setSearchParams(newParams, { replace: false });
      }
    },
    [genre, rank, selectedTrack, searchParams, setSearchParams]
  );

  const openTrack = useCallback(
    (track: Track) => {
      setHasInteracted(false);

      const defaultPlayer = getDefaultPlayer(track);

      const newParams = new URLSearchParams(searchParams);
      newParams.set("genre", genre);
      newParams.set("rank", rank);
      newParams.set("isrc", track.isrc);

      if (defaultPlayer) {
        newParams.set("player", defaultPlayer);
      } else {
        newParams.delete("player");
      }

      setSearchParams(newParams, { replace: false });
      setSelectedTrack(track);
      setIsMediaPlayerOpen(true);
    },
    [genre, rank, searchParams, setSearchParams, getDefaultPlayer]
  );

  const onPlayingStateChange = useCallback((playing: boolean) => {
    setHasInteracted(true);
    setIsPlaying(playing);
  }, []);

  return {
    genre,
    rank,
    isrc,
    player: activePlayer,
    selectedTrack,
    isMediaPlayerOpen,
    hasInteracted,
    setGenre,
    setRank,
    openTrack,
    closeMediaPlayer,
    setPlayer,
    onPlayingStateChange,
  };
}
