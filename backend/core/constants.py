from enum import Enum


class GenreName(str, Enum):
    DANCE = "dance"
    RAP = "rap"
    COUNTRY = "country"
    POP = "pop"


class ServiceName(str, Enum):
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    SOUNDCLOUD = "soundcloud"
    YOUTUBE = "youtube"
    TUNEMELD = "tunemeld"


GENRE_CONFIGS: dict[str, dict] = {
    GenreName.POP.value: {
        "display_name": "Pop",
        "icon_url": "/images/genre-pop.png",
        "order": 0,
        "links": {
            ServiceName.APPLE_MUSIC.value: "https://music.apple.com/us/playlist/a-list-pop/pl.5ee8333dbe944d9f9151e97d92d1ead9",
            ServiceName.SOUNDCLOUD.value: "https://soundcloud.com/soundcloud-shine/sets/ear-candy-fresh-pop-picks",
            ServiceName.SPOTIFY.value: "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
        },
    },
    GenreName.DANCE.value: {
        "display_name": "Dance/Electronic",
        "icon_url": "/images/genre-dance.png",
        "order": 1,
        "links": {
            ServiceName.APPLE_MUSIC.value: "https://music.apple.com/us/playlist/dancexl/pl.6bf4415b83ce4f3789614ac4c3675740",
            ServiceName.SOUNDCLOUD.value: "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-new-edm-hits",
            ServiceName.SPOTIFY.value: "https://open.spotify.com/playlist/37i9dQZF1DX4dyzvuaRJ0n",
        },
    },
    GenreName.RAP.value: {
        "display_name": "Hip-Hop/Rap",
        "icon_url": "/images/genre-rap.png",
        "order": 2,
        "links": {
            ServiceName.APPLE_MUSIC.value: "https://music.apple.com/us/playlist/rap-life/pl.abe8ba42278f4ef490e3a9fc5ec8e8c5",
            ServiceName.SOUNDCLOUD.value: "https://soundcloud.com/soundcloud-hustle/sets/drippin-best-rap-right-now",
            ServiceName.SPOTIFY.value: "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd",
        },
    },
    GenreName.COUNTRY.value: {
        "display_name": "Country",
        "icon_url": "/images/genre-country.png",
        "order": 3,
        "links": {
            ServiceName.APPLE_MUSIC.value: "https://music.apple.com/us/playlist/todays-country/pl.87bb5b36a9bd49db8c975607452bfa2b",
            ServiceName.SOUNDCLOUD.value: "https://soundcloud.com/trending-music-us/sets/country",
            ServiceName.SPOTIFY.value: "https://open.spotify.com/playlist/37i9dQZF1DX1lVhptIYRda",
        },
    },
}

PLAYLIST_GENRES: list[str] = [genre.value for genre in GenreName]
SERVICES: list[str] = [service.value for service in ServiceName]


class RankType(str, Enum):
    TUNEMELD_RANK = "tunemeld_rank"
    SPOTIFY_VIEWS_RANK = "spotify_views_rank"
    YOUTUBE_VIEWS_RANK = "youtube_views_rank"


DEFAULT_RANK_TYPE = RankType.TUNEMELD_RANK


RANK_CONFIGS: dict[str, dict] = {
    RankType.TUNEMELD_RANK.value: {
        "display_name": "Tunemeld Rank",
        "sort_field": "tunemeld-rank",
        "sort_order": "asc",
        "data_field": "tunemeldRank",
        "icon_url": "/images/tunemeld.png",
    },
    RankType.SPOTIFY_VIEWS_RANK.value: {
        "display_name": "Spotify Views",
        "sort_field": "spotify-views",
        "sort_order": "desc",
        "data_field": "spotifyCurrentViewCount",
        "icon_url": "/images/spotify_logo.png",
    },
    RankType.YOUTUBE_VIEWS_RANK.value: {
        "display_name": "YouTube Views",
        "sort_field": "youtube-views",
        "sort_order": "desc",
        "data_field": "youtubeCurrentViewCount",
        "icon_url": "/images/youtube_logo.png",
    },
}

SERVICE_CONFIGS: dict[str, dict] = {
    ServiceName.APPLE_MUSIC.value: {
        "base_url": "https://apple-music24.p.rapidapi.com/playlist1/",
        "host": "apple-music24.p.rapidapi.com",
        "param_key": "url",
        "playlist_base_url": "https://music.apple.com/us/playlist/",
        "display_name": "Apple Music",
        "icon_url": "/images/apple_music_logo.png",
    },
    ServiceName.SOUNDCLOUD.value: {
        "base_url": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "host": "soundcloud-scraper.p.rapidapi.com",
        "param_key": "playlist",
        "playlist_base_url": "https://soundcloud.com/",
        "display_name": "SoundCloud",
        "icon_url": "/images/soundcloud_logo.png",
    },
    ServiceName.SPOTIFY.value: {
        "playlist_base_url": "https://open.spotify.com/playlist/",
        "display_name": "Spotify",
        "icon_url": "/images/spotify_logo.png",
    },
    ServiceName.YOUTUBE.value: {
        "display_name": "YouTube",
        "icon_url": "/images/youtube_logo.png",
    },
    ServiceName.TUNEMELD.value: {
        "display_name": "tunemeld",
        "icon_url": "/images/tunemeld.png",
    },
}
