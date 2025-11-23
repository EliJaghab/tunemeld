import React, { useEffect, useState } from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { MediaSquare } from "@/v2/components/shared/MediaSquare";
import { CloseButton } from "@/v2/components/shared/CloseButton";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";
import { ServicePlayer } from "@/v2/components/media-player/players/ServicePlayer";
import { MiniPlayer } from "@/v2/components/media-player/mini-player/MiniPlayer";
import { ChevronDown } from "@/v2/components/shared/icons/ChevronDown";
import { PLAYER, type PlayerValue } from "@/v2/constants";
import type { Track } from "@/types";

interface MediaPlayerProps {
  track: Track | null;
  activePlayer?: PlayerValue | null;
  isOpen: boolean;
  onClose: () => void;
  onServiceClick?: (player: PlayerValue) => void;
}

function MediaPlayerHeader({ track }: { track: Track }) {
  return (
    <div className={clsx("flex flex-row items-center gap-4 w-full pr-24")}>
      {track.albumCoverUrl && (
        <div
          className={clsx("flex-shrink-0 overflow-hidden rounded-lg")}
          style={{
            width: "64px",
            height: "64px",
          }}
        >
          <MediaSquare
            src={track.albumCoverUrl}
            type="image"
            alt={`${track.trackName} cover`}
          />
        </div>
      )}

      <div className={clsx("flex-1 min-w-0 flex flex-col gap-1")}>
        <div
          className={clsx(
            "font-semibold text-base desktop:text-lg",
            "text-black dark:text-white",
            "line-clamp-1"
          )}
        >
          {track.trackName}
        </div>
        <div
          className={clsx(
            "text-sm desktop:text-base",
            "text-black/70 dark:text-white/70",
            "line-clamp-1"
          )}
        >
          {track.artistName}
        </div>
      </div>
    </div>
  );
}

function MediaPlayerControls({
  onCollapse,
  onClose,
}: {
  onCollapse: () => void;
  onClose: () => void;
}) {
  return (
    <div className="absolute top-4 right-4 flex gap-2 z-10">
      <button
        onClick={onCollapse}
        aria-label="Collapse media player"
        className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center",
          `bg-white/60 hover:bg-white/80 active:bg-white/90 dark:bg-gray-700/60
          dark:hover:bg-gray-600/80 backdrop-blur-md`,
          "text-black dark:text-white transition-colors",
          "border border-white/20 dark:border-gray-600/20",
          "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]"
        )}
      >
        <ChevronDown className="w-4 h-4" />
      </button>
      <CloseButton
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        ariaLabel="Close media player"
        position="relative"
      />
    </div>
  );
}

function MediaPlayerServiceIcons({
  track,
  onServiceClick,
}: {
  track: Track;
  onServiceClick?: (player: PlayerValue) => void;
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
      className={clsx(
        "mt-4 self-end",
        "bg-white/60 dark:bg-gray-700/60 backdrop-blur-md",
        "border border-white/20 dark:border-gray-600/20",
        "rounded-2xl",
        "px-2 pt-2 pb-0.5 desktop:px-2.5 desktop:pt-2.5 desktop:pb-1",
        "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]",
        "overflow-visible",
        "flex items-center"
      )}
    >
      <div className={clsx("flex items-center gap-2 desktop:gap-2.5")}>
        {serviceData.map((item) => {
          if (!item.source) return null;

          const playerMapping: Record<string, PlayerValue> = {
            spotify: PLAYER.SPOTIFY,
            apple_music: PLAYER.APPLE_MUSIC,
            soundcloud: PLAYER.SOUNDCLOUD,
            youtube: PLAYER.YOUTUBE,
          };

          const player = playerMapping[item.source.name.toLowerCase()];

          return (
            <ServiceIcon
              key={item.source.name}
              source={item.source}
              rank={item.rank ?? undefined}
              size="md"
              badgeSize="md"
              onClick={() => {
                if (onServiceClick && player) {
                  onServiceClick(player);
                }
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

export function MediaPlayer({
  track,
  activePlayer,
  isOpen,
  onClose,
  onServiceClick,
}: MediaPlayerProps): React.ReactElement | null {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      setIsCollapsed(false);
    }
  }, [track, isOpen]);

  useEffect(() => {
    setIsPlaying(false);
  }, [track]);

  if (!isOpen || !track) return null;

  const handleTogglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const canControl =
    activePlayer === PLAYER.YOUTUBE || activePlayer === PLAYER.SOUNDCLOUD;

  const showMiniPlayer = isCollapsed;

  return (
    <>
      <div
        className={clsx(
          "fixed bottom-0 left-0 right-0 z-[1001]",
          "px-4 pb-4 desktop:px-6 desktop:pb-6",
          "pointer-events-none", // Wrapper is always pointer-events-none
          showMiniPlayer ? "invisible" : "visible"
        )}
      >
        <div className={clsx("max-w-4xl mx-auto", "pointer-events-auto")}>
          <GlassSurface
            width="100%"
            height="auto"
            borderRadius={32}
            backgroundOpacity={0.5}
            borderWidth={0.5}
            blur={20}
            className="!items-start !justify-start"
          >
            <div
              className={clsx(
                "p-5 text-left w-full min-h-[100px]",
                "flex flex-col w-full relative",
                "min-h-min"
              )}
            >
              <div
                className={clsx(
                  "absolute top-0 left-0 right-0 h-px",
                  `bg-gradient-to-r from-transparent via-white/40
                  to-transparent`
                )}
              />

              <MediaPlayerControls
                onCollapse={() => setIsCollapsed(true)}
                onClose={onClose}
              />

              <MediaPlayerHeader track={track} />

              {activePlayer && (
                <ServicePlayer
                  track={track}
                  activePlayer={activePlayer}
                  playing={isPlaying}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                />
              )}

              <MediaPlayerServiceIcons
                track={track}
                onServiceClick={onServiceClick}
              />
            </div>
          </GlassSurface>
        </div>
      </div>

      {showMiniPlayer && (
        <MiniPlayer
          track={track}
          isPlaying={isPlaying}
          canControl={canControl}
          onTogglePlay={handleTogglePlay}
          onExpand={() => setIsCollapsed(false)}
          onClose={() => {
            onClose();
          }}
        />
      )}
    </>
  );
}
