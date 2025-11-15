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

export type ServiceMetadata = {
  href: string;
  description?: string | undefined;
  coverUrl?: string | undefined;
};

export const GENRE = {
  POP: "pop",
  DANCE: "dance",
  RAP: "rap",
  COUNTRY: "country",
} as const;

export type GenreValue = (typeof GENRE)[keyof typeof GENRE];
