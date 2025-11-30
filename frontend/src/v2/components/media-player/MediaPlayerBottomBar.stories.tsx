import React from "react";
import type { Meta, StoryObj } from "@storybook/react";
import { MediaPlayerBottomBar } from "./MediaPlayerBottomBar";
import type { Track, ServiceSource } from "@/types";

const mockSpotifySource: ServiceSource = {
  name: "spotify",
  displayName: "Spotify",
  url: "https://open.spotify.com/track/example",
  iconUrl: "/images/spotify_logo.png",
};

const mockYouTubeSource: ServiceSource = {
  name: "youtube",
  displayName: "YouTube",
  url: "https://youtube.com/watch?v=example",
  iconUrl: "/images/youtube_logo.png",
};

const mockSoundCloudSource: ServiceSource = {
  name: "soundcloud",
  displayName: "SoundCloud",
  url: "https://soundcloud.com/example",
  iconUrl: "/images/soundcloud_logo.png",
};

const mockAppleMusicSource: ServiceSource = {
  name: "apple_music",
  displayName: "Apple Music",
  url: "https://music.apple.com/track/example",
  iconUrl: "/images/apple_music_logo.png",
};

const mockTrack: Track = {
  isrc: "USRC17607839",
  trackName: "Test Track",
  artistName: "Test Artist",
  albumName: "Test Album",
  albumCoverUrl: "/images/album_art_placeholder.png",
  youtubeSource: mockYouTubeSource,
  youtubeUrl: "https://youtube.com/watch?v=example",
  youtubeRank: 1,
  spotifySource: mockSpotifySource,
  spotifyUrl: "https://open.spotify.com/track/example",
  spotifyRank: 2,
  soundcloudSource: mockSoundCloudSource,
  soundcloudUrl: "https://soundcloud.com/example",
  soundcloudRank: 3,
  appleMusicSource: mockAppleMusicSource,
  appleMusicUrl: "https://music.apple.com/track/example",
  appleMusicRank: 4,
};

const meta = {
  title: "Components/MediaPlayer/MediaPlayerBottomBar",
  component: MediaPlayerBottomBar,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof MediaPlayerBottomBar>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    track: mockTrack,
    isPlaying: false,
    canControl: true,
    onTogglePlay: () => console.log("Toggle play"),
    onServiceClick: (player) => console.log("Service clicked:", player),
  },
  render: (args) => (
    <div className="w-full max-w-4xl p-8">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-black dark:text-white mb-4">
          Play Button (Paused State)
        </h3>
        <MediaPlayerBottomBar {...args} />
      </div>
    </div>
  ),
};

export const Playing: Story = {
  args: {
    track: mockTrack,
    isPlaying: true,
    canControl: true,
    onTogglePlay: () => console.log("Toggle play"),
    onServiceClick: (player) => console.log("Service clicked:", player),
  },
  render: (args) => (
    <div className="w-full max-w-4xl p-8">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-black dark:text-white mb-4">
          Pause Button (Playing State)
        </h3>
        <MediaPlayerBottomBar {...args} />
      </div>
    </div>
  ),
};

export const NoPlayControl: Story = {
  args: {
    track: mockTrack,
    isPlaying: false,
    canControl: false,
    onTogglePlay: () => console.log("Toggle play"),
    onServiceClick: (player) => console.log("Service clicked:", player),
  },
  render: (args) => (
    <div className="w-full max-w-4xl p-8">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-black dark:text-white mb-4">
          No Play Control (Service Icons Only)
        </h3>
        <MediaPlayerBottomBar {...args} />
      </div>
    </div>
  ),
};

export const Interactive: Story = {
  render: () => {
    const [isPlaying, setIsPlaying] = React.useState(false);

    return (
      <div className="w-full max-w-4xl p-8">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-black dark:text-white mb-4">
            Interactive Play/Pause Toggle
          </h3>
          <MediaPlayerBottomBar
            track={mockTrack}
            isPlaying={isPlaying}
            canControl={true}
            onTogglePlay={() => setIsPlaying(!isPlaying)}
            onServiceClick={(player) => console.log("Service clicked:", player)}
          />
          <p className="mt-4 text-sm text-black dark:text-white">
            Current state: {isPlaying ? "Playing" : "Paused"}
          </p>
        </div>
      </div>
    );
  },
};

export const WithBorder: Story = {
  args: {
    track: mockTrack,
    isPlaying: false,
    canControl: true,
    onTogglePlay: () => console.log("Toggle play"),
    onServiceClick: (player) => console.log("Service clicked:", player),
  },
  render: (args) => (
    <div className="w-full max-w-4xl p-8">
      <div
        className="bg-white dark:bg-gray-800 p-6 rounded-lg border-2
          border-red-500"
      >
        <h3 className="text-lg font-semibold text-black dark:text-white mb-4">
          With Border (Check Alignment)
        </h3>
        <div className="border-2 border-blue-500">
          <MediaPlayerBottomBar {...args} />
        </div>
        <p className="mt-4 text-xs text-black dark:text-white">
          Red border = container, Blue border = component
        </p>
      </div>
    </div>
  ),
};
