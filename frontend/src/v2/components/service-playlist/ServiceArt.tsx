import React from "react";
import { useServiceMetadata } from "@/v2/ServiceMetadataContext";
import { SERVICE, type ServiceName } from "@/v2/constants";
import { MediaSquare } from "@/v2/components/shared/MediaSquare";
import { PlaylistDescription } from "@/v2/components/service-playlist/PlaylistDescription";
import clsx from "clsx";

interface ServiceArtProps {
  serviceName: ServiceName;
  onOpenModal: (content: {
    serviceDisplayName?: string;
    playlistName?: string;
    description?: string;
    playlistUrl?: string;
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
      className={clsx(
        "service w-full rounded-media",
        "border-2 border-gray-500 dark:border-gray-600",
        "p-2 desktop:p-4",
        "!bg-transparent"
      )}
    >
      <div className={clsx("mb-2.5 desktop:mb-4")}>
        {isLoading ? (
          <div
            className={clsx(
              "aspect-square w-full",
              "bg-black/10 dark:bg-white/10",
              "rounded-media"
            )}
          ></div>
        ) : (
          coverUrl && (
            <a
              id={`${serviceName}-cover-link`}
              href={metadata?.href ?? "#"}
              target="_blank"
              rel="noreferrer"
              className={clsx("block")}
            >
              <MediaSquare
                src={coverUrl}
                type={coverType}
                alt={`${serviceName} playlist cover`}
              />
            </a>
          )
        )}
      </div>

      <div
        className={clsx(
          "mb-2 desktop:mb-4",
          "min-h-[48px] desktop:min-h-[72px]",
          "flex flex-col justify-center"
        )}
      >
        {isLoading ? (
          <div className={clsx("space-y-2")}>
            <div
              className={clsx(
                "h-5 desktop:h-6",
                "bg-black/10 dark:bg-white/10 rounded",
                "w-3/4"
              )}
            ></div>
            <div
              className={clsx(
                "h-4 desktop:h-5",
                "bg-black/10 dark:bg-white/10 rounded",
                "w-1/2"
              )}
            ></div>
          </div>
        ) : (
          (serviceDisplayName || playlistName) && (
            <>
              {serviceDisplayName && (
                <button
                  onClick={() =>
                    onOpenModal({
                      ...(serviceDisplayName && {
                        serviceDisplayName,
                      }),
                      ...(playlistName && {
                        playlistName,
                      }),
                      ...(metadata?.description && {
                        description: metadata.description,
                      }),
                      ...(metadata?.href && {
                        playlistUrl: metadata.href,
                      }),
                    })
                  }
                  className={clsx(
                    "text-sm desktop:text-xl font-bold",
                    "text-black dark:text-white",
                    "leading-snug desktop:leading-tight",
                    "tracking-tight",
                    "text-left truncate w-full"
                  )}
                  title={serviceDisplayName + "'s"}
                >
                  {serviceDisplayName}
                  's
                </button>
              )}
              {playlistName && (
                <button
                  onClick={() =>
                    onOpenModal({
                      ...(serviceDisplayName && {
                        serviceDisplayName,
                      }),
                      ...(playlistName && {
                        playlistName,
                      }),
                      ...(metadata?.description && {
                        description: metadata.description,
                      }),
                      ...(metadata?.href && {
                        playlistUrl: metadata.href,
                      }),
                    })
                  }
                  className={clsx(
                    "text-xs desktop:text-lg font-semibold",
                    "text-black dark:text-white",
                    "leading-snug desktop:leading-tight",
                    "tracking-tight",
                    "mt-0.5 desktop:mt-1",
                    "truncate w-full text-left"
                  )}
                  title={playlistName}
                >
                  {playlistName}
                </button>
              )}
            </>
          )
        )}
      </div>

      <div
        className={clsx("border-t border-black/20 dark:border-white/30")}
      ></div>

      <div className={clsx("mt-3 desktop:mt-4 h-[80px] desktop:h-[96px]")}>
        {isLoading ? (
          <div
            className={clsx("flex h-full flex-col justify-between space-y-2")}
          >
            <div
              className={clsx(
                "h-4 desktop:h-5",
                "bg-black/10 dark:bg-white/10 rounded",
                "w-full"
              )}
            ></div>
            <div
              className={clsx(
                "h-4 desktop:h-5",
                "bg-black/10 dark:bg-white/10 rounded",
                "w-full"
              )}
            ></div>
            <div
              className={clsx(
                "h-4 desktop:h-5",
                "bg-black/10 dark:bg-white/10 rounded",
                "w-full"
              )}
            ></div>
            <div
              className={clsx(
                "h-4 desktop:h-5",
                "bg-black/10 dark:bg-white/10 rounded",
                "w-3/4"
              )}
            ></div>
          </div>
        ) : (
          <PlaylistDescription
            key={metadata?.description}
            description={metadata?.description}
            serviceName={serviceName}
            playlistName={playlistName}
            serviceDisplayName={serviceDisplayName}
            onOpenModal={(content) =>
              onOpenModal({
                ...content,
                ...(metadata?.href && {
                  playlistUrl: metadata.href,
                }),
              })
            }
            className={clsx("h-full")}
          />
        )}
      </div>
    </div>
  );
}
