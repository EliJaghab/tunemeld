import React, { useRef, useEffect, useState } from "react";
import clsx from "clsx";
import { IconButton } from "@/v2/components/shared/IconButton";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";
import type { Track } from "@/types";
import type { PlayerValue } from "@/v2/constants";

interface MediaPlayerBottomBarProps {
  track: Track;
  isPlaying: boolean;
  canControl: boolean;
  onTogglePlay: () => void;
  onServiceClick?: (player: PlayerValue) => void;
}

export function MediaPlayerBottomBar({
  track,
  isPlaying,
  canControl,
  onTogglePlay,
  onServiceClick,
}: MediaPlayerBottomBarProps): React.ReactElement {
  const serviceIconsRef = useRef<HTMLDivElement>(null);
  const [playButtonHeight, setPlayButtonHeight] = useState<number | undefined>(
    undefined
  );

  const serviceData = [
    {
      source: track.youtubeSource,
      rank: track.youtubeRank,
    },
    {
      source: track.spotifySource,
      rank: track.spotifyRank,
    },
    {
      source: track.soundcloudSource,
      rank: track.soundcloudRank,
    },
    {
      source: track.appleMusicSource,
      rank: track.appleMusicRank,
    },
  ];

  useEffect(() => {
    if (!serviceIconsRef.current) return;

    const measureHeight = () => {
      if (serviceIconsRef.current) {
        const height = serviceIconsRef.current.offsetHeight;
        if (height > 0) {
          setPlayButtonHeight(height);
        }
      }
    };

    measureHeight();

    const resizeObserver = new ResizeObserver(() => {
      measureHeight();
    });

    if (serviceIconsRef.current) {
      resizeObserver.observe(serviceIconsRef.current);
    }

    window.addEventListener("resize", measureHeight);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", measureHeight);
    };
  }, [track]);

  return (
    <div
      className={clsx(
        "flex items-center justify-end gap-2 desktop:gap-3",
        "overflow-visible",
        "w-full",
        "flex-nowrap"
      )}
    >
      {canControl && (
        <IconButton
          onClick={onTogglePlay}
          icon={isPlaying ? "pause" : "play"}
          ariaLabel={isPlaying ? "Pause" : "Play"}
          variant="glass-container"
          size="sm"
          containerPadding="p-2 desktop:p-2.5"
          borderRadius="rounded-2xl"
          height={playButtonHeight}
          className="flex-shrink-0 z-10 relative"
        />
      )}

      <div className="flex-shrink min-w-0" ref={serviceIconsRef}>
        <div
          className={clsx(
            "bg-white/60 dark:bg-gray-700/60 backdrop-blur-md",
            "border border-white/20 dark:border-gray-600/20",
            "rounded-2xl",
            "px-2 desktop:px-2.5",
            "pt-2 desktop:pt-2.5 pb-0.5 desktop:pb-0.5",
            "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]",
            "flex items-center"
          )}
        >
          <div
            className={clsx(
              "flex items-center gap-2 desktop:gap-2.5",
              "flex-shrink min-w-0"
            )}
          >
            {serviceData.map((item) => {
              if (!item.source) return null;

              return (
                <ServiceIcon
                  key={item.source.name}
                  source={item.source}
                  rank={item.rank}
                  size="md"
                  onClick={
                    onServiceClick
                      ? () => onServiceClick(item.source!.name)
                      : undefined
                  }
                />
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
