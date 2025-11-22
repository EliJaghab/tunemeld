import type { Rank } from "@/types";

export const THEME = {
  LIGHT: "light",
  DARK: "dark",
} as const;

export type ThemeValue = (typeof THEME)[keyof typeof THEME];

export const isThemeValue = (value: unknown): value is ThemeValue =>
  value === THEME.LIGHT || value === THEME.DARK;

export const THEME_STORAGE_KEY = "tunemeld:v2:theme";

export const SERVICE = {
  APPLE_MUSIC: "apple_music",
  SOUNDCLOUD: "soundcloud",
  SPOTIFY: "spotify",
} as const;

export type ServiceName = (typeof SERVICE)[keyof typeof SERVICE];

export const PLAYER = {
  YOUTUBE: "youtube",
  SPOTIFY: "spotify",
  APPLE_MUSIC: "apple_music",
  SOUNDCLOUD: "soundcloud",
} as const;

export type PlayerValue = (typeof PLAYER)[keyof typeof PLAYER];

export const isPlayerValue = (value: unknown): value is PlayerValue =>
  Object.values(PLAYER).includes(value as PlayerValue);

export type ServiceMetadata = {
  href: string;
  description?: string | undefined;
  coverUrl?: string | undefined;
  playlistName?: string | undefined;
  serviceDisplayName?: string | undefined;
};

export const GENRE = {
  POP: "pop",
  DANCE: "dance",
  RAP: "rap",
  COUNTRY: "country",
} as const;

export type GenreValue = (typeof GENRE)[keyof typeof GENRE];

export const RANK = {
  TUNEMELD_RANK: "tunemeld-rank",
  TOTAL_PLAYS: "total-plays",
  TRENDING: "trending",
} as const;

export type RankValue = (typeof RANK)[keyof typeof RANK];

export const RANKS: Rank[] = [
  {
    name: RANK.TUNEMELD_RANK,
    displayName: "TuneMeld Rank",
    sortField: RANK.TUNEMELD_RANK,
    sortOrder: "asc",
    isDefault: true,
    dataField: "tunemeldRank",
  },
  {
    name: RANK.TOTAL_PLAYS,
    displayName: "Total Plays",
    sortField: RANK.TOTAL_PLAYS,
    sortOrder: "desc",
    isDefault: false,
    dataField: "totalCurrentPlayCount",
  },
  {
    name: RANK.TRENDING,
    displayName: "Trending",
    sortField: RANK.TRENDING,
    sortOrder: "desc",
    isDefault: false,
    dataField: "totalWeeklyChangePercentage",
  },
];
