import React from "react";
import clsx from "clsx";
import { ServiceIcon } from "@/v2/components/playlist/shared/ServiceIcon";
import type { Track } from "@/types";

interface SeenOnProps {
  track: Track;
}

export function SeenOn({ track }: SeenOnProps) {
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
  ].filter((item) => {
    return item.source && item.rank !== null && item.rank !== undefined;
  });

  if (serviceData.length === 0) {
    return null;
  }

  return (
    <div
      className={clsx(
        "track-sources flex justify-center items-center",
        "gap-1 desktop:gap-2"
      )}
    >
      {serviceData.map(
        (item) =>
          item.source && (
            <ServiceIcon
              key={item.source.name}
              source={item.source}
              rank={item.rank}
            />
          )
      )}
    </div>
  );
}
