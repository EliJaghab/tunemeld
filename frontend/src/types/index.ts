// AUTO-GENERATED FILE - DO NOT EDIT
// Generated from backend/domain_types/types.py
// Run 'npm run generate-types' to regenerate

export interface ButtonLabel {
  button_type: string;
  context?: string | null;
  title?: string | null;
  aria_label?: string | null;
}

export interface ServiceSource {
  name: string;
  display_name: string;
  url: string;
  icon_url: string;
}

export interface Track {
  isrc: string;
  track_name: string;
  artist_name: string;
  full_track_name: string;
  full_artist_name: string;
  album_name?: string | null;
  album_cover_url?: string | null;
  spotify_url?: string | null;
  apple_music_url?: string | null;
  soundcloud_url?: string | null;
  youtube_url?: string | null;
  tunemeld_rank: number;
  spotify_rank?: number | null;
  apple_music_rank?: number | null;
  soundcloud_rank?: number | null;
  spotify_source?: ServiceSource | null;
  apple_music_source?: ServiceSource | null;
  soundcloud_source?: ServiceSource | null;
  youtube_source?: ServiceSource | null;
  track_detail_url_spotify?: string | null;
  track_detail_url_apple_music?: string | null;
  track_detail_url_soundcloud?: string | null;
  track_detail_url_youtube?: string | null;
  total_current_play_count?: number | null;
  total_weekly_change_percentage?: number | null;
  spotify_current_play_count?: number | null;
  youtube_current_play_count?: number | null;
  button_labels?: ButtonLabel[];
  id?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface Playlist {
  genre_name: string;
  service_name: string;
  tracks?: Track[];
  playlist_name?: string | null;
  playlist_cover_url?: string | null;
  playlist_cover_description_text?: string | null;
  playlist_url?: string | null;
  service_icon_url?: string | null;
  updated_at?: string | null;
}

export interface PlayCount {
  isrc: string;
  youtube_current_play_count?: number | null;
  spotify_current_play_count?: number | null;
  total_current_play_count?: number | null;
  youtube_current_play_count_abbreviated?: string | null;
  spotify_current_play_count_abbreviated?: string | null;
  total_current_play_count_abbreviated?: string | null;
  total_weekly_change_percentage?: number | null;
  total_weekly_change_percentage_formatted?: string | null;
}

export interface Rank {
  name: string;
  display_name: string;
  sort_field: string;
  sort_order: string;
  is_default: boolean;
  data_field: string;
}

export interface ServiceConfig {
  id: number;
  name: string;
  display_name: string;
  icon_url: string;
}

export interface Genre {
  id: number;
  name: string;
  display_name: string;
  icon_class: string;
  icon_url: string;
}

// Frontend-specific types
export interface State {
  currentColumn: string;
  currentOrder: string;
  currentGenre: string;
  currentTheme: string;
  modals: Record<string, { modal: HTMLElement; overlay: HTMLElement }>;
}
