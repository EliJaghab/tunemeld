export const SERVICE_NAMES = {
  SPOTIFY: "spotify",
  APPLE_MUSIC: "apple_music",
  SOUNDCLOUD: "soundcloud",
  YOUTUBE: "youtube",
  TUNEMELD: "tunemeld",
  TOTAL: "total",
} as const;

// The rank that preserves backend-computed positions
export const TUNEMELD_RANK_FIELD = "tunemeld-rank";

// Shimmer layout types
export const SHIMMER_TYPES = {
  TUNEMELD: "tunemeld", // Shows 3 service icons
  TOTAL_PLAYS: "total-plays", // Shows 1 play count value
  TRENDING: "trending", // Shows 1 trending value
} as const;

export type ShimmerType = (typeof SHIMMER_TYPES)[keyof typeof SHIMMER_TYPES];

// Playlist placeholder IDs
export const PLAYLIST_PLACEHOLDERS = {
  MAIN: "main-playlist-data-placeholder",
  SERVICE_SUFFIX: "-data-placeholder",
} as const;
