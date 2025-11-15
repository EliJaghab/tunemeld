import React from "react";
import { useServiceMetadata } from "@/v2/ServiceMetadataContext";
import { SERVICE, type ServiceName } from "@/v2/constants";
import { MediaSquare } from "@/v2/components/MediaSquare";

export function ServiceArt({
  serviceName,
}: {
  serviceName: ServiceName;
}): React.ReactElement {
  const metadataRecord = useServiceMetadata();
  const metadata = metadataRecord?.[serviceName];
  const coverUrl = metadata?.coverUrl;
  const coverType =
    serviceName === SERVICE.APPLE_MUSIC && coverUrl?.endsWith(".m3u8")
      ? "video"
      : "image";

  return (
    <div id={serviceName} className="service flex-1 min-w-0">
      <a
        id={`${serviceName}-cover-link`}
        href={metadata?.href ?? "#"}
        target="_blank"
        rel="noreferrer"
      >
        {coverUrl && (
          <MediaSquare
            src={coverUrl}
            type={coverType}
            alt={`${serviceName} playlist cover`}
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
