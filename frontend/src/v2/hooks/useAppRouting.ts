import { useState, useEffect, useCallback, useMemo } from "react";
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
  setGenre: (genre: GenreValue) => void;
  setRank: (rank: string) => void;
  openTrack: (track: Track, playlistTracks: Track[]) => void;
  closeMediaPlayer: () => void;
  setPlayer: (player: PlayerValue) => void;
}

export function useAppRouting(playlistTracks: Track[]): UseAppRoutingReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [isMediaPlayerOpen, setIsMediaPlayerOpen] = useState(false);

  const genreParam = searchParams.get("genre");
  const genre: GenreValue = useMemo(() => {
    const validGenre =
      genreParam && Object.values(GENRE).includes(genreParam as GenreValue)
        ? (genreParam as GenreValue)
        : GENRE.POP;
    return validGenre;
  }, [genreParam]);

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
  const playerParam = searchParams.get("player");
  const player: PlayerValue | null =
    playerParam && Object.values(PLAYER).includes(playerParam as PlayerValue)
      ? (playerParam as PlayerValue)
      : null;

  const getDefaultPlayer = useCallback((track: Track): PlayerValue | null => {
    if (track.youtubeSource) return PLAYER.YOUTUBE;
    if (track.spotifySource) return PLAYER.SPOTIFY;
    if (track.appleMusicSource) return PLAYER.APPLE_MUSIC;
    if (track.soundcloudSource) return PLAYER.SOUNDCLOUD;
    return null;
  }, []);

  const setGenre = useCallback(
    (newGenre: GenreValue) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("genre", newGenre);
      setSearchParams(newParams, { replace: false });
    },
    [searchParams, setSearchParams]
  );

  const setRank = useCallback(
    (newRank: string) => {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("rank", newRank);
      if (isrc) {
        newParams.set("isrc", isrc);
      }
      if (player) {
        newParams.set("player", player);
      }
      setSearchParams(newParams, { replace: false });
    },
    [searchParams, isrc, player, setSearchParams]
  );

  const openTrack = useCallback(
    (track: Track, tracks: Track[]) => {
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

  const closeMediaPlayer = useCallback(() => {
    setIsMediaPlayerOpen(false);
    setSelectedTrack(null);
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("isrc");
    newParams.delete("player");
    setSearchParams(newParams, { replace: true });
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

  useEffect(() => {
    if (isrc && playlistTracks.length > 0) {
      const track = playlistTracks.find((t) => t.isrc === isrc);
      if (track && track.isrc !== selectedTrack?.isrc) {
        setSelectedTrack(track);
        setIsMediaPlayerOpen(true);
      }
    } else if (!isrc && selectedTrack) {
      setIsMediaPlayerOpen(false);
      setSelectedTrack(null);
    }
  }, [isrc, playlistTracks, selectedTrack]);

  return {
    genre,
    rank,
    isrc,
    player,
    selectedTrack,
    isMediaPlayerOpen,
    setGenre,
    setRank,
    openTrack,
    closeMediaPlayer,
    setPlayer,
  };
}
