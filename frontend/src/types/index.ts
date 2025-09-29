export interface Genre {
  id: string;
  name: string;
  displayName: string;
  iconUrl: string;
  buttonLabels?: ButtonLabel[];
}

export interface ButtonLabel {
  buttonType: string;
  context?: string;
  title?: string;
  ariaLabel?: string;
}

export interface Track {
  tunemeldRank: number;
  spotifyRank?: number;
  appleMusicRank?: number;
  soundcloudRank?: number;
  isrc: string;
  trackName: string;
  artistName: string;
  fullTrackName: string;
  fullArtistName: string;
  albumName: string;
  albumCoverUrl: string;
  youtubeUrl?: string;
  spotifyUrl?: string;
  appleMusicUrl?: string;
  soundcloudUrl?: string;
  buttonLabels?: ButtonLabel[];
  spotifySource?: ServiceSource;
  appleMusicSource?: ServiceSource;
  soundcloudSource?: ServiceSource;
  youtubeSource?: ServiceSource;
  seenOnSpotify: boolean;
  seenOnAppleMusic: boolean;
  seenOnSoundcloud: boolean;
  trackDetailUrlSpotify?: string;
  trackDetailUrlAppleMusic?: string;
  trackDetailUrlSoundcloud?: string;
  trackDetailUrlYoutube?: string;
  // Play count data (added dynamically)
  totalCurrentPlayCount?: number;
  totalWeeklyChangePercentage?: number;
  spotifyCurrentPlayCount?: number;
  youtubeCurrentPlayCount?: number;
}

export interface ServiceSource {
  name: string;
  displayName: string;
  url: string;
  iconUrl: string;
}

export interface Playlist {
  genreName: string;
  serviceName: string;
  tracks: Track[];
  playlistName?: string;
  playlistCoverUrl?: string;
  playlistCoverDescriptionText?: string;
  playlistUrl?: string;
  serviceIconUrl?: string;
}

export interface PlayCount {
  isrc: string;
  youtubeCurrentPlayCount?: number;
  spotifyCurrentPlayCount?: number;
  totalCurrentPlayCount?: number;
  youtubeCurrentPlayCountAbbreviated?: string;
  spotifyCurrentPlayCountAbbreviated?: string;
  totalCurrentPlayCountAbbreviated?: string;
  totalWeeklyChangePercentage?: number;
  totalWeeklyChangePercentageFormatted?: string;
}

export interface ServiceConfig {
  name: string;
  displayName: string;
  iconUrl: string;
  urlField: string;
  sourceField: string;
  buttonLabels?: ButtonLabel[];
}

export interface IframeConfig {
  serviceName: string;
  embedBaseUrl: string;
  embedParams: Record<string, string>;
  allow: string;
  height: number;
  referrerPolicy: string;
}

export interface Rank {
  name: string;
  displayName: string;
  sortField: string;
  sortOrder: string;
  isDefault: boolean;
  dataField: string;
}

export interface State {
  currentColumn: string;
  currentOrder: string;
  currentGenre: string;
  currentTheme: string;
  modals: Record<string, { modal: HTMLElement; overlay: HTMLElement }>;
}
