// AUTO-GENERATED FILE - DO NOT EDIT
// Generated from backend/domain_types/types.py
// Run 'npm run generate-types' to regenerate

export interface ButtonLabel {
  buttonType: string;
  context?: string | null;
  title?: string | null;
  ariaLabel?: string | null;
}

export interface ServiceSource {
  name: string;
  displayName: string;
  url: string;
  iconUrl: string;
}

export interface Track {
  isrc: string;
  trackName: string;
  artistName: string;
  fullTrackName: string;
  fullArtistName: string;
  albumName?: string | null;
  albumCoverUrl?: string | null;
  spotifyUrl?: string | null;
  appleMusicUrl?: string | null;
  soundcloudUrl?: string | null;
  youtubeUrl?: string | null;
  tunemeldRank: number;
  spotifyRank?: number | null;
  appleMusicRank?: number | null;
  soundcloudRank?: number | null;
  spotifySource?: ServiceSource | null;
  appleMusicSource?: ServiceSource | null;
  soundcloudSource?: ServiceSource | null;
  youtubeSource?: ServiceSource | null;
  trackDetailUrlSpotify?: string | null;
  trackDetailUrlAppleMusic?: string | null;
  trackDetailUrlSoundcloud?: string | null;
  trackDetailUrlYoutube?: string | null;
  totalCurrentPlayCount?: number | null;
  totalWeeklyChangePercentage?: number | null;
  spotifyCurrentPlayCount?: number | null;
  youtubeCurrentPlayCount?: number | null;
  buttonLabels?: ButtonLabel[];
  id?: number | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface Playlist {
  genreName: string;
  serviceName: string;
  tracks?: Track[];
  playlistName?: string | null;
  playlistCoverUrl?: string | null;
  playlistCoverDescriptionText?: string | null;
  playlistUrl?: string | null;
  serviceDisplayName?: string | null;
  serviceIconUrl?: string | null;
  updatedAt?: string | null;
}

export interface PlayCount {
  isrc: string;
  youtubeCurrentPlayCount?: number | null;
  spotifyCurrentPlayCount?: number | null;
  totalCurrentPlayCount?: number | null;
  youtubeCurrentPlayCountAbbreviated?: string | null;
  spotifyCurrentPlayCountAbbreviated?: string | null;
  totalCurrentPlayCountAbbreviated?: string | null;
  totalWeeklyChangePercentage?: number | null;
  totalWeeklyChangePercentageFormatted?: string | null;
}

export interface Rank {
  name: string;
  displayName: string;
  sortField: string;
  sortOrder: string;
  isDefault: boolean;
  dataField: string;
}

export interface ServiceConfig {
  id: number;
  name: string;
  displayName: string;
  iconUrl: string;
  urlField: string;
  sourceField: string;
  buttonLabels?: ButtonLabel[];
}

export interface Genre {
  id: number;
  name: string;
  displayName: string;
  iconUrl: string;
  buttonLabels?: ButtonLabel[];
}

// Frontend-specific types
export interface IframeConfig {
  serviceName: string;
  embedBaseUrl: string;
  embedParams?: string;
  allow?: string;
  height?: string;
  referrerPolicy?: string;
}

export interface ButtonLabels {
  closePlayer: ButtonLabel[];
  themeToggleLight: ButtonLabel[];
  themeToggleDark: ButtonLabel[];
  acceptTerms: ButtonLabel[];
  moreButtonAppleMusic: ButtonLabel[];
  moreButtonSoundcloud: ButtonLabel[];
  moreButtonSpotify: ButtonLabel[];
  moreButtonYoutube: ButtonLabel[];
}
