import React, { useEffect } from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { MediaSquare } from "@/v2/components/shared/MediaSquare";
import { CloseButton } from "@/v2/components/shared/CloseButton";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";
import { PLAYER, type PlayerValue } from "@/v2/constants";
import type { Track } from "@/types";

interface MediaPlayerProps {
  track: Track | null;
  isOpen: boolean;
  onClose: () => void;
  onServiceClick?: (player: PlayerValue) => void;
}

export function MediaPlayer({
  track,
  isOpen,
  onClose,
  onServiceClick,
}: MediaPlayerProps): React.ReactElement | null {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen || !track) return null;

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

  return (
    <div
      className={clsx(
        "fixed bottom-0 left-0 right-0 z-[1001]",
        "px-4 pb-4 desktop:px-6 desktop:pb-6",
        "pointer-events-none"
      )}
    >
      <div className={clsx("max-w-4xl mx-auto pointer-events-auto")}>
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
              "!flex !flex-row !items-center !justify-start !gap-4",
              "relative"
            )}
          >
            <div
              className={clsx(
                "absolute top-0 left-0 right-0 h-px",
                "bg-gradient-to-r from-transparent via-white/40 to-transparent"
              )}
            />

            <CloseButton
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              ariaLabel="Close media player"
              position="top-right"
            />

            {serviceData.length > 0 && (
              <div
                className={clsx(
                  "absolute bottom-4 right-4",
                  "bg-white/60 dark:bg-gray-700/60 backdrop-blur-md",
                  "border border-white/20 dark:border-gray-600/20",
                  "rounded-2xl",
                  "px-2 pt-2 pb-0.5 desktop:px-2.5 desktop:pt-2.5 desktop:pb-1",
                  "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]",
                  "overflow-visible",
                  "flex items-center"
                )}
              >
                <div
                  className={clsx(
                    "flex items-center gap-2 desktop:gap-2.5 relative"
                  )}
                >
                  {serviceData.map((item) => {
                    if (!item.source) return null;

                    const playerMapping: Record<string, PlayerValue> = {
                      spotify: PLAYER.SPOTIFY,
                      apple_music: PLAYER.APPLE_MUSIC,
                      soundcloud: PLAYER.SOUNDCLOUD,
                      youtube: PLAYER.YOUTUBE,
                    };

                    const player =
                      playerMapping[item.source.name.toLowerCase()];

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
            )}

            {track.albumCoverUrl && (
              <div
                className={clsx("flex-shrink-0 overflow-hidden")}
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

            <div className={clsx("flex-1 min-w-0 flex flex-col gap-1 pr-20")}>
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
        </GlassSurface>
      </div>
    </div>
  );
}
