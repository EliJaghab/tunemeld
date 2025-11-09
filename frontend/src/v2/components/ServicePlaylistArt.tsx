import React from "react";
import { useServiceMetadata } from "@/v2/ServiceMetadataContext";
import { SERVICE, type ServiceName } from "@/v2/constants";

export function ServicePlaylistArt({
  serviceName,
}: {
  serviceName: ServiceName;
}): React.ReactElement {
  const metadata = useServiceMetadata()[serviceName];
  const isVideo = serviceName === SERVICE.APPLE_MUSIC && metadata?.videoSrc;

  return (
    <div id={serviceName} className="service">
      <a
        id={`${serviceName}-cover-link`}
        href={metadata?.href ?? "#"}
        target="_blank"
        rel="noreferrer"
      >
        {isVideo ? (
          <div
            id={`${serviceName}-video-container`}
            className="video-container"
          >
            <video
              id={`${serviceName}-video`}
              src={metadata?.videoSrc}
              muted
              autoPlay
              loop
              playsInline
              controlsList="nodownload nofullscreen noremoteplayback"
            />
          </div>
        ) : (
          <div
            id={`${serviceName}-image-placeholder`}
            className="image-placeholder"
          />
        )}
      </a>
      <div
        id={`${serviceName}-title-description`}
        className="title-description"
      >
        {metadata?.description}
      </div>
    </div>
  );
}
