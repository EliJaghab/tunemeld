import { create } from "zustand";
import {
  GENRE,
  RANKS,
  RANK,
  PLAYER,
  type GenreValue,
  type PlayerValue,
} from "@/v2/constants";
import type { Track } from "@/types";

interface MediaPlayerState {
  currentTrack: Track | null;
  activePlayer: PlayerValue | null;
  isOpen: boolean;
  isMinimized: boolean;
  isPlaying: boolean;
  hasInteracted: boolean;
  wasExplicitlyClosed: boolean;
  genre: GenreValue;
  rank: string;
  playlistTracks: Track[];
  urlUpdateCallback: ((params: URLSearchParams) => void) | null;
  pendingIsrc: string | null;
  pendingPlayer: PlayerValue | null;
}

interface MediaPlayerActions {
  setTrack: (track: Track) => void;
  setActivePlayer: (player: PlayerValue | null) => void;
  open: () => void;
  close: () => void;
  minimize: () => void;
  expand: () => void;
  togglePlay: () => void;
  setPlaying: (isPlaying: boolean) => void;
  setHasInteracted: (hasInteracted: boolean) => void;
  setWasExplicitlyClosed: (wasClosed: boolean) => void;
  reset: () => void;
  setGenre: (genre: GenreValue) => void;
  setRank: (rank: string) => void;
  setPlaylistTracks: (tracks: Track[]) => void;
  setUrlUpdateCallback: (
    callback: ((params: URLSearchParams) => void) | null
  ) => void;
  openTrack: (track: Track, player?: PlayerValue | null) => void;
  handleGenreChange: (newGenre: GenreValue) => void;
  loadFirstTrackForGenre: (tracks: Track[]) => void;
  syncFromUrl: (searchParams: URLSearchParams) => void;
  getDefaultPlayer: (track: Track) => PlayerValue | null;
}

type MediaPlayerStore = MediaPlayerState & MediaPlayerActions;

const initialState: MediaPlayerState = {
  currentTrack: null,
  activePlayer: null,
  isOpen: false,
  isMinimized: true,
  isPlaying: false,
  hasInteracted: false,
  wasExplicitlyClosed: false,
  genre: GENRE.POP,
  rank: RANKS.find((r) => r.isDefault)?.sortField || RANK.TUNEMELD_RANK,
  playlistTracks: [],
  urlUpdateCallback: null,
  pendingIsrc: null,
  pendingPlayer: null,
};

const updateUrl = (state: MediaPlayerState) => {
  if (state.urlUpdateCallback) {
    const params = new URLSearchParams();
    params.set("genre", state.genre);
    params.set("rank", state.rank);
    if (state.currentTrack && state.isOpen && !state.wasExplicitlyClosed) {
      params.set("isrc", state.currentTrack.isrc);
      if (state.activePlayer) {
        params.set("player", state.activePlayer);
      }
    }
    state.urlUpdateCallback(params);
  }
};

export const useMediaPlayerStore = create<MediaPlayerStore>((set, get) => ({
  ...initialState,

  setTrack: (track: Track) =>
    set((state) => {
      const newState = {
        ...state,
        currentTrack: track,
        isOpen: true,
        wasExplicitlyClosed: false,
        isMinimized: true,
        isPlaying: false,
      };
      updateUrl(newState);
      return newState;
    }),

  setActivePlayer: (player: PlayerValue | null) =>
    set((state) => {
      const newState = { ...state, activePlayer: player };
      updateUrl(newState);
      return newState;
    }),

  open: () =>
    set((state) => {
      const newState = {
        ...state,
        isOpen: true,
        wasExplicitlyClosed: false,
      };
      updateUrl(newState);
      return newState;
    }),

  close: () =>
    set((state) => {
      const newState = {
        ...state,
        isOpen: false,
        isPlaying: false,
        wasExplicitlyClosed: true,
        currentTrack: null,
        activePlayer: null,
      };
      updateUrl(newState);
      return newState;
    }),

  minimize: () => set({ isMinimized: true }),

  expand: () => set({ isMinimized: false }),

  togglePlay: () =>
    set((state) => ({
      isPlaying: !state.isPlaying,
      hasInteracted: true,
    })),

  setPlaying: (isPlaying: boolean) =>
    set((state) => ({
      isPlaying,
      hasInteracted: state.hasInteracted || isPlaying,
    })),

  setHasInteracted: (hasInteracted: boolean) => set({ hasInteracted }),

  setWasExplicitlyClosed: (wasClosed: boolean) =>
    set({ wasExplicitlyClosed: wasClosed }),

  reset: () => set(initialState),

  setGenre: (genre: GenreValue) =>
    set((state) => {
      const newState = { ...state, genre };
      updateUrl(newState);
      return newState;
    }),

  setRank: (rank: string) =>
    set((state) => {
      const newState = { ...state, rank };
      updateUrl(newState);
      return newState;
    }),

  setPlaylistTracks: (tracks: Track[]) => set({ playlistTracks: tracks }),

  setUrlUpdateCallback: (
    callback: ((params: URLSearchParams) => void) | null
  ) => set({ urlUpdateCallback: callback }),

  getDefaultPlayer: (track: Track): PlayerValue | null => {
    if (track.youtubeSource) return PLAYER.YOUTUBE;
    if (track.spotifySource) return PLAYER.SPOTIFY;
    if (track.appleMusicSource) return PLAYER.APPLE_MUSIC;
    if (track.soundcloudSource) return PLAYER.SOUNDCLOUD;
    return null;
  },

  openTrack: (track: Track, player?: PlayerValue | null) =>
    set((state) => {
      const defaultPlayer = get().getDefaultPlayer(track);
      const selectedPlayer = player ?? defaultPlayer;
      const newState = {
        ...state,
        currentTrack: track,
        activePlayer: selectedPlayer,
        isOpen: true,
        wasExplicitlyClosed: false,
        isMinimized: true,
        isPlaying: false,
        hasInteracted: true,
      };
      updateUrl(newState);
      return newState;
    }),

  handleGenreChange: (newGenre: GenreValue) =>
    set((state) => {
      if (!state.isOpen || state.wasExplicitlyClosed) {
        const newState = { ...state, genre: newGenre };
        updateUrl(newState);
        return newState;
      }

      if (state.hasInteracted && state.currentTrack) {
        const newState = { ...state, genre: newGenre };
        updateUrl(newState);
        return newState;
      }

      const firstTrack =
        state.playlistTracks.length > 0 ? state.playlistTracks[0] : null;
      if (firstTrack) {
        const defaultPlayer = get().getDefaultPlayer(firstTrack);
        const newState = {
          ...state,
          genre: newGenre,
          currentTrack: firstTrack,
          activePlayer: defaultPlayer,
          isOpen: true,
        };
        updateUrl(newState);
        return newState;
      } else {
        const newState = {
          ...state,
          genre: newGenre,
          currentTrack: null,
          activePlayer: null,
          isOpen: false,
        };
        updateUrl(newState);
        return newState;
      }
    }),

  loadFirstTrackForGenre: (tracks: Track[]) =>
    set((state) => {
      const firstTrack = tracks.length > 0 ? tracks[0] : null;

      if (state.pendingIsrc) {
        const pendingTrack = tracks.find((t) => t.isrc === state.pendingIsrc);
        if (pendingTrack) {
          const player =
            state.pendingPlayer || get().getDefaultPlayer(pendingTrack);
          const newState = {
            ...state,
            playlistTracks: tracks,
            currentTrack: pendingTrack,
            activePlayer: player,
            isOpen: true,
            wasExplicitlyClosed: false,
            isMinimized: true,
            pendingIsrc: null,
            pendingPlayer: null,
          };
          updateUrl(newState);
          return newState;
        }
        return { ...state, playlistTracks: tracks };
      }

      if (!firstTrack || state.wasExplicitlyClosed || state.hasInteracted) {
        return { ...state, playlistTracks: tracks };
      }

      if (state.currentTrack && state.isOpen) {
        return { ...state, playlistTracks: tracks };
      }

      const defaultPlayer = get().getDefaultPlayer(firstTrack);
      const newState = {
        ...state,
        playlistTracks: tracks,
        currentTrack: firstTrack,
        activePlayer: defaultPlayer,
        isOpen: true,
        wasExplicitlyClosed: false,
        isMinimized: true,
      };
      updateUrl(newState);
      return newState;
    }),

  syncFromUrl: (searchParams: URLSearchParams) => {
    const genreParam = searchParams.get("genre");
    const genre =
      genreParam && Object.values(GENRE).includes(genreParam as GenreValue)
        ? (genreParam as GenreValue)
        : GENRE.POP;

    const rank =
      searchParams.get("rank") ||
      RANKS.find((r) => r.isDefault)?.sortField ||
      RANK.TUNEMELD_RANK;

    const isrc = searchParams.get("isrc");
    const playerParam = searchParams.get("player");
    const player =
      playerParam && Object.values(PLAYER).includes(playerParam as PlayerValue)
        ? (playerParam as PlayerValue)
        : null;

    set((state) => {
      const updates: Partial<MediaPlayerState> = {
        genre,
        rank,
      };

      if (isrc) {
        const track = state.playlistTracks.find((t) => t.isrc === isrc);
        if (track) {
          updates.currentTrack = track;
          updates.activePlayer = player || get().getDefaultPlayer(track);
          updates.isOpen = true;
          updates.wasExplicitlyClosed = false;
          updates.isMinimized = true;
          updates.pendingIsrc = null;
          updates.pendingPlayer = null;
        } else {
          updates.pendingIsrc = isrc;
          updates.pendingPlayer = player;
        }
      } else if (state.currentTrack && state.isOpen) {
        updates.currentTrack = null;
        updates.activePlayer = null;
        updates.isOpen = false;
      }

      return { ...state, ...updates };
    });
  },
}));

export const useCurrentTrack = () =>
  useMediaPlayerStore((state) => state.currentTrack);

export const usePlayerState = () =>
  useMediaPlayerStore((state) => ({
    isOpen: state.isOpen,
    isMinimized: state.isMinimized,
    isPlaying: state.isPlaying,
    hasInteracted: state.hasInteracted,
    wasExplicitlyClosed: state.wasExplicitlyClosed,
  }));

export const usePlayerActions = () =>
  useMediaPlayerStore((state) => ({
    setTrack: state.setTrack,
    setActivePlayer: state.setActivePlayer,
    open: state.open,
    close: state.close,
    minimize: state.minimize,
    expand: state.expand,
    togglePlay: state.togglePlay,
    setPlaying: state.setPlaying,
    setHasInteracted: state.setHasInteracted,
    setWasExplicitlyClosed: state.setWasExplicitlyClosed,
    reset: state.reset,
  }));
