import React, { useEffect } from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { MediaSquare } from "@/v2/components/shared/MediaSquare";
import { CloseButton } from "@/v2/components/shared/CloseButton";
import { ServicePlayer } from "@/v2/components/media-player/players/ServicePlayer";
import { MiniPlayer } from "@/v2/components/media-player/mini-player/MiniPlayer";
import { MediaPlayerBottomBar } from "@/v2/components/media-player/MediaPlayerBottomBar";
import { ChevronDown } from "@/v2/components/shared/icons/ChevronDown";
import { useMediaPlayer } from "@/v2/contexts/MediaPlayerContext";
import { PLAYER } from "@/v2/constants";
import type { Track } from "@/types";

function MediaPlayerHeader({ track }: { track: Track }) {
  return (
    <div className={clsx("flex flex-row items-center gap-4 w-full pr-24")}>
      {track.albumCoverUrl && (
        <div
          className={clsx("flex-shrink-0 overflow-hidden rounded-full")}
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

export function MediaPlayer(): React.ReactElement | null {
  const {
    track,
    activePlayer,
    isOpen,
    isMinimized,
    isPlaying,
    expand,
    collapse,
    togglePlay,
    setPlaying,
    onClose,
    onServiceClick,
  } = useMediaPlayer();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  const hasYouTube = !!track?.youtubeSource;
  const canControl = hasYouTube && activePlayer === PLAYER.YOUTUBE;

  if (!isOpen || !track) {
    return null;
  }

  return (
    <>
      {(canControl || !isMinimized) && (
        <div
          className={clsx(
            "fixed bottom-0 left-0 right-0 z-[1001]",
            "px-4 pb-4 desktop:px-6 desktop:pb-6",
            isMinimized && canControl
              ? "opacity-0 pointer-events-none -z-10"
              : ""
          )}
          style={
            isMinimized && canControl
              ? {
                  position: "fixed",
                  left: "-9999px",
                  top: "-9999px",
                  width: "1px",
                  height: "1px",
                  overflow: "hidden",
                }
              : undefined
          }
        >
          <div className={clsx("max-w-4xl mx-auto")}>
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
                  "min-h-min overflow-visible",
                  "overflow-x-visible"
                )}
              >
                <div
                  className={clsx(
                    "absolute top-0 left-0 right-0 h-px",
                    `bg-gradient-to-r from-transparent via-white/40
                    to-transparent`
                  )}
                />

                <MediaPlayerControls onCollapse={collapse} onClose={onClose} />

                <MediaPlayerHeader track={track} />

                {activePlayer && (
                  <div className="w-full">
                    <ServicePlayer
                      key={
                        canControl
                          ? `youtube-player-persistent-${track.isrc}`
                          : undefined
                      }
                      track={track}
                      activePlayer={activePlayer}
                      playing={isPlaying}
                      onPlay={() => setPlaying(true)}
                      onPause={() => setPlaying(false)}
                    />
                  </div>
                )}

                <div className="mt-4 self-end">
                  <MediaPlayerBottomBar
                    track={track}
                    isPlaying={isPlaying}
                    canControl={canControl}
                    onTogglePlay={togglePlay}
                    onServiceClick={onServiceClick}
                  />
                </div>
              </div>
            </GlassSurface>
          </div>
        </div>
      )}

      {isMinimized && (
        <MiniPlayer
          track={track}
          isPlaying={isPlaying}
          canControl={canControl}
          onTogglePlay={togglePlay}
          onExpand={expand}
          onClose={onClose}
        />
      )}
    </>
  );
}
