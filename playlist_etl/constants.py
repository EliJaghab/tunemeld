from enum import Enum


class GenreName(str, Enum):
    DANCE = "dance"
    RAP = "rap"
    COUNTRY = "country"
    POP = "pop"


class ServiceName(str, Enum):
    SPOTIFY = "Spotify"
    APPLE_MUSIC = "AppleMusic"
    SOUNDCLOUD = "SoundCloud"
    YOUTUBE = "YouTube"


GENRE_DISPLAY_NAMES: dict[str, str] = {
    GenreName.DANCE: "Dance/Electronic",
    GenreName.RAP: "Hip-Hop/Rap",
    GenreName.COUNTRY: "Country",
    GenreName.POP: "Pop",
}

PLAYLIST_GENRES: list[str] = [genre.value for genre in GenreName]
SERVICES: list[str] = [service.value for service in ServiceName]

SERVICE_CONFIGS: dict[str, dict] = {
    ServiceName.APPLE_MUSIC: {
        "base_url": "https://apple-music24.p.rapidapi.com/playlist1/",
        "host": "apple-music24.p.rapidapi.com",
        "param_key": "url",
        "playlist_base_url": "https://music.apple.com/us/playlist/",
        "display_name": "Apple Music",
        "icon_url": "images/apple_music_logo.png",
        "links": {
            GenreName.COUNTRY: "https://music.apple.com/us/playlist/todays-country/pl.87bb5b36a9bd49db8c975607452bfa2b",
            GenreName.DANCE: "https://music.apple.com/us/playlist/dancexl/pl.6bf4415b83ce4f3789614ac4c3675740",
            GenreName.POP: "https://music.apple.com/us/playlist/a-list-pop/pl.5ee8333dbe944d9f9151e97d92d1ead9",
            GenreName.RAP: "https://music.apple.com/us/playlist/rap-life/pl.abe8ba42278f4ef490e3a9fc5ec8e8c5",
        },
    },
    ServiceName.SOUNDCLOUD: {
        "base_url": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "host": "soundcloud-scraper.p.rapidapi.com",
        "param_key": "playlist",
        "playlist_base_url": "https://soundcloud.com/",
        "display_name": "SoundCloud",
        "icon_url": "images/soundcloud_logo.png",
        "links": {
            GenreName.COUNTRY: "https://soundcloud.com/trending-music-us/sets/country",
            GenreName.DANCE: "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-new-edm-hits",
            GenreName.POP: "https://soundcloud.com/nightsoul-ong-kh/sets/pop-hits-2024-top-100-trending",
            GenreName.RAP: "https://soundcloud.com/soundcloud-hustle/sets/drippin-best-rap-right-now",
        },
    },
    ServiceName.SPOTIFY: {
        "base_url": "https://spotify23.p.rapidapi.com/playlist_tracks/",
        "host": "spotify23.p.rapidapi.com",
        "param_key": "id",
        "playlist_base_url": "https://open.spotify.com/playlist/",
        "display_name": "Spotify",
        "icon_url": "images/spotify_logo.png",
        "links": {
            GenreName.COUNTRY: "https://open.spotify.com/playlist/37i9dQZF1DX1lVhptIYRda",
            GenreName.DANCE: "https://open.spotify.com/playlist/37i9dQZF1DX4dyzvuaRJ0n",
            GenreName.POP: "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            GenreName.RAP: "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd",
        },
    },
    ServiceName.YOUTUBE: {
        "display_name": "YouTube",
        "icon_url": "images/youtube_logo.png",
    },
}
