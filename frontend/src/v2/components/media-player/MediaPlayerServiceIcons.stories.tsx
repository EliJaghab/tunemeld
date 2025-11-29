import type { Meta, StoryObj } from "@storybook/react";
import type { Track, ServiceSource } from "@/types";

const mockSpotifySource: ServiceSource = {
  name: "spotify",
  displayName: "Spotify",
  url: "https://open.spotify.com/track/example",
  iconUrl: "/images/spotify_logo.png",
};

const mockAppleMusicSource: ServiceSource = {
  name: "apple_music",
  displayName: "Apple Music",
  url: "https://music.apple.com/track/example",
  iconUrl: "/images/apple_music_logo.png",
};

const mockSoundCloudSource: ServiceSource = {
  name: "soundcloud",
  displayName: "SoundCloud",
  url: "https://soundcloud.com/track/example",
  iconUrl: "/images/soundcloud_logo.png",
};

const mockYouTubeSource: ServiceSource = {
  name: "youtube",
  displayName: "YouTube",
  url: "https://youtube.com/watch?v=example",
  iconUrl: "/images/youtube_logo.png",
};

const mockTrackAllServices: Track = {
  isrc: "TEST123456789",
  trackName: "Test Track",
  artistName: "Test Artist",
  fullTrackName: "Test Track (Extended Mix)",
  fullArtistName: "Test Artist feat. Another Artist",
  albumName: "Test Album",
  albumCoverUrl: "https://via.placeholder.com/300",
  tunemeldRank: 1,
  spotifyRank: 5,
  appleMusicRank: 12,
  soundcloudRank: 8,
  spotifySource: mockSpotifySource,
  appleMusicSource: mockAppleMusicSource,
  soundcloudSource: mockSoundCloudSource,
  youtubeSource: mockYouTubeSource,
  spotifyUrl: "https://open.spotify.com/track/example",
  appleMusicUrl: "https://music.apple.com/track/example",
  soundcloudUrl: "https://soundcloud.com/track/example",
  youtubeUrl: "https://youtube.com/watch?v=example",
};

function MediaPlayerServiceIcons({
  track,
  onServiceClick,
}: {
  track: Track;
  onServiceClick?: (player: string) => void;
}) {
  const serviceData = [
    {
      source: track.spotifySource,
      rank: track.spotifyRank,
    },
    {
      source: track.appleMusicSource,
      rank: track.appleMusicRank,
    },
    {
      source: track.soundcloudSource,
      rank: track.soundcloudRank,
    },
    {
      source: track.youtubeSource,
      rank: null,
    },
  ].filter((item) => {
    return item.source !== null && item.source !== undefined;
  });

  if (serviceData.length === 0) return null;

  return (
    <div
      className="bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border
        border-white/20 dark:border-gray-600/20 rounded-2xl px-2 desktop:px-2.5
        pt-2 desktop:pt-2.5 pb-0.5 desktop:pb-0.5
        shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]
        overflow-visible flex items-center flex-shrink-0"
    >
      <div className="flex items-center gap-2 desktop:gap-2.5">
        {serviceData.map((item) => {
          if (!item.source) return null;

          const isDoubleDigit =
            item.rank !== null && item.rank !== undefined && item.rank >= 10;

          return (
            <div key={item.source.name} className="relative inline-block">
              <button
                onClick={() => {
                  if (onServiceClick) {
                    onServiceClick(item.source!.name);
                  }
                }}
                className="cursor-pointer"
                aria-label={`${item.source.displayName}${item.rank ? ` - Rank ${item.rank}` : ""}`}
              >
                <img
                  src={item.source.iconUrl}
                  alt={item.source.displayName}
                  className="w-6 h-6 desktop:w-[30px] desktop:h-[30px] block
                    object-contain"
                />
              </button>
              {item.rank !== null && item.rank !== undefined && (
                <span
                  className={`absolute -top-1 -right-1 desktop:-top-[7px]
                  desktop:-right-[7px] flex items-center justify-center
                  text-white font-bold text-[9px] desktop:text-[11px]
                  leading-none z-50 rounded-full bg-badge-red
                  shadow-[0_1px_3px_rgba(0,0,0,0.3)] px-0.5 ${
                    isDoubleDigit
                      ? `min-w-[14px] w-[18px] h-[14px] desktop:min-w-[18px]
                        desktop:w-[22px] desktop:h-[18px]
                        desktop:rounded-[11px]`
                      : "w-[14px] h-[14px] desktop:w-[18px] desktop:h-[18px]"
                  }`}
                >
                  {item.rank}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

const meta = {
  title: "MediaPlayer/ServiceIcons",
  component: MediaPlayerServiceIcons,
  parameters: {
    layout: "centered",
    backgrounds: {
      default: "dark",
      values: [
        { name: "light", value: "#f0f0f0" },
        { name: "dark", value: "#1a1a1a" },
      ],
    },
  },
  tags: ["autodocs"],
} satisfies Meta<typeof MediaPlayerServiceIcons>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    track: mockTrackAllServices,
    onServiceClick: (player) => console.log("Clicked:", player),
  },
};

export const PaddingTest: Story = {
  render: () => (
    <div className="p-8 space-y-6">
      <div>
        <h3 className="text-sm font-semibold mb-2 text-gray-300">
          Visual Padding Test - Check if badges overflow outside white border
        </h3>
        <div className="border-2 border-dashed border-white inline-block">
          <MediaPlayerServiceIcons
            track={mockTrackAllServices}
            onServiceClick={(player) => console.log("Clicked:", player)}
          />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2 text-gray-300">
          Vertical Centering Test - Card should be centered between gray lines
        </h3>
        <div className="flex items-center gap-4">
          <div className="w-px h-20 bg-gray-500" />
          <MediaPlayerServiceIcons
            track={mockTrackAllServices}
            onServiceClick={(player) => console.log("Clicked:", player)}
          />
          <div className="w-px h-20 bg-gray-500" />
        </div>
      </div>
    </div>
  ),
};
