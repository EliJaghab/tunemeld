export const SERVICE_NAMES = {
  SPOTIFY: "spotify",
  APPLE_MUSIC: "apple_music",
  SOUNDCLOUD: "soundcloud",
  YOUTUBE: "youtube",
  TUNEMELD: "tunemeld",
  TOTAL: "total",
} as const;

export type ServiceName = (typeof SERVICE_NAMES)[keyof typeof SERVICE_NAMES];

export const GENRE_NAMES = {
  DANCE: "dance",
  RAP: "rap",
  COUNTRY: "country",
  POP: "pop",
} as const;

export type GenreName = (typeof GENRE_NAMES)[keyof typeof GENRE_NAMES];

// The rank that preserves backend-computed positions
export const TUNEMELD_RANK_FIELD = "tunemeld-rank";

// Shimmer layout types
export const SHIMMER_TYPES = {
  TUNEMELD: "tunemeld",
  PLAYCOUNT: "playcount",
} as const;

export type ShimmerType = (typeof SHIMMER_TYPES)[keyof typeof SHIMMER_TYPES];

// Playlist placeholder IDs
export const PLAYLIST_PLACEHOLDERS = {
  MAIN: "main-playlist-data-placeholder",
  SERVICE_SUFFIX: "-data-placeholder",
} as const;
