import React from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { MediaSquare } from "@/v2/components/shared/MediaSquare";
import type { Track } from "@/types";

interface MiniPlayerProps {
  track: Track;
  onExpand: () => void;
  onClose: () => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  canControl?: boolean;
}

export function MiniPlayer({
  track,
  onExpand,
  onClose,
  isPlaying,
  onTogglePlay,
  canControl = false,
}: MiniPlayerProps): React.ReactElement {
  return (
    <div
      className={clsx(
        "fixed bottom-4 left-4 right-4 z-[1001]",
        "flex items-end gap-2 desktop:gap-3",
        "max-w-4xl mx-auto"
      )}
    >
      {/* Main Mini Player Bar */}
      <div className="flex-1 cursor-pointer" onClick={onExpand}>
        <GlassSurface
          width="100%"
          height="64px"
          borderRadius={32}
          backgroundOpacity={0.6}
          borderWidth={0.5}
          blur={20}
          className="!items-start !justify-start"
        >
          <div
            className={clsx(
              "w-full h-full px-2 pl-2 pr-4",
              "flex items-center justify-between gap-3"
            )}
          >
            {/* Left: Art + Info */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {track.albumCoverUrl && (
                <div
                  className="w-12 h-12 flex-shrink-0 overflow-hidden
                    rounded-full"
                >
                  <MediaSquare
                    src={track.albumCoverUrl}
                    type="image"
                    alt={track.trackName}
                  />
                </div>
              )}
              <div className="flex flex-col justify-center min-w-0">
                <div
                  className="font-semibold text-sm text-black dark:text-white
                    truncate"
                >
                  {track.trackName}
                </div>
                <div
                  className="text-xs text-black/70 dark:text-white/70 truncate"
                >
                  {track.artistName}
                </div>
              </div>
            </div>

            {canControl && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  onTogglePlay();
                }}
                onMouseDown={(e) => e.stopPropagation()}
                onTouchStart={(e) => e.stopPropagation()}
                aria-label={isPlaying ? "Pause" : "Play"}
                className="h-12 flex items-center justify-center flex-shrink-0
                  p-0 m-0 border-0 bg-transparent cursor-pointer"
              >
                {isPlaying ? (
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-6 h-6 desktop:w-7 desktop:h-7 text-black
                      dark:text-white"
                  >
                    <rect x="6" y="4" width="4" height="16" rx="1" />
                    <rect x="14" y="4" width="4" height="16" rx="1" />
                  </svg>
                ) : (
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-6 h-6 desktop:w-7 desktop:h-7 text-black
                      dark:text-white"
                  >
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>
            )}
          </div>
        </GlassSurface>
      </div>

      {/* Separate Close Button */}
      <div className="flex-shrink-0" style={{ height: "64px", width: "64px" }}>
        <GlassSurface
          width="100%"
          height="100%"
          borderRadius={32}
          backgroundOpacity={0.6}
          borderWidth={0.5}
          blur={20}
          className="!items-center !justify-center cursor-pointer"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            onClose();
          }}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-black dark:text-white pointer-events-none"
          >
            <path d="M18 6L6 18" />
            <path d="M6 6l12 12" />
          </svg>
        </GlassSurface>
      </div>
    </div>
  );
}
