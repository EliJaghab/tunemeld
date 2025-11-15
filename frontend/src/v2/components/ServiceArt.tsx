import React from "react";
import { useServiceMetadata } from "@/v2/ServiceMetadataContext";
import { SERVICE, type ServiceName } from "@/v2/constants";
import { MediaSquare } from "@/v2/components/MediaSquare";
import { PlaylistDescription } from "@/v2/components/PlaylistDescription";

interface ServiceArtProps {
  serviceName: ServiceName;
  onOpenModal: (content: {
    serviceDisplayName?: string;
    playlistName?: string;
    description?: string;
  }) => void;
  isLoading?: boolean;
}

export function ServiceArt({
  serviceName,
  onOpenModal,
  isLoading = false,
}: ServiceArtProps): React.ReactElement {
  const metadataRecord = useServiceMetadata();
  const metadata = metadataRecord?.[serviceName];
  const coverUrl = metadata?.coverUrl;
  const coverType =
    serviceName === SERVICE.APPLE_MUSIC && coverUrl?.endsWith(".m3u8")
      ? "video"
      : "image";

  const serviceDisplayName = metadata?.serviceDisplayName;
  const playlistName = metadata?.playlistName;

  return (
    <div
      id={serviceName}
      className="service flex-1 min-w-0 rounded-media bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 shadow-lg p-4"
    >
      {isLoading ? (
        <>
          <div className="block mb-3">
            <div className="aspect-square w-full bg-black/10 dark:bg-white/10 rounded-2xl"></div>
          </div>
          <div className="mb-3">
            <div className="h-6 bg-black/10 dark:bg-white/10 rounded w-3/4"></div>
            <div className="h-5 bg-black/10 dark:bg-white/10 rounded mt-1 w-1/2"></div>
          </div>
          <div className="border-t border-black/20 dark:border-white/30"></div>
          <div className="title-description relative">
            <div className="h-[21.6px] bg-black/10 dark:bg-white/10 rounded w-full"></div>
            <div className="h-[21.6px] bg-black/10 dark:bg-white/10 rounded w-full"></div>
            <div className="h-[21.6px] bg-black/10 dark:bg-white/10 rounded w-full"></div>
            <div className="h-[21.6px] bg-black/10 dark:bg-white/10 rounded w-3/4"></div>
          </div>
        </>
      ) : (
        <>
          <a
            id={`${serviceName}-cover-link`}
            href={metadata?.href ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="block mb-3"
          >
            {coverUrl && (
              <MediaSquare
                src={coverUrl}
                type={coverType}
                alt={`${serviceName} playlist cover`}
              />
            )}
          </a>
          {(serviceDisplayName || playlistName) && (
            <div className="mb-3">
              {serviceDisplayName && (
                <h2 className="text-xl font-bold text-black dark:text-white leading-tight">
                  {serviceDisplayName}'s
                </h2>
              )}
              {playlistName && (
                <h3 className="text-base font-semibold text-black dark:text-white leading-tight mt-1 tracking-tighter whitespace-nowrap overflow-hidden">
                  {playlistName}
                </h3>
              )}
            </div>
          )}
          <div className="border-t border-black/20 dark:border-white/30"></div>
          <PlaylistDescription
            key={metadata?.description}
            description={metadata?.description}
            serviceName={serviceName}
            playlistName={playlistName}
            serviceDisplayName={serviceDisplayName}
            onOpenModal={onOpenModal}
          />
        </>
      )}
    </div>
  );
}
