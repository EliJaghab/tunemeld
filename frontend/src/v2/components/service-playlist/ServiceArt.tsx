import React from "react";
import { useServiceMetadata } from "@/v2/ServiceMetadataContext";
import {
  SERVICE,
  type ServiceName,
  type ServiceMetadata,
} from "@/v2/constants";
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

interface ModalContent {
  serviceDisplayName?: string;
  playlistName?: string;
  description?: string;
  playlistUrl?: string;
}

function buildModalContent(
  metadata: ServiceMetadata | undefined,
  serviceDisplayName?: string,
  playlistName?: string
): ModalContent {
  return {
    ...(serviceDisplayName && { serviceDisplayName }),
    ...(playlistName && { playlistName }),
    ...(metadata?.description && { description: metadata.description }),
    ...(metadata?.href && { playlistUrl: metadata.href }),
  };
}

function CoverShimmer(): React.ReactElement {
  return (
    <div
      className={clsx(
        "aspect-square w-full",
        "bg-black/10 dark:bg-white/10",
        "rounded-media"
      )}
      style={{ minHeight: 0 }}
    ></div>
  );
}

function TitleShimmer(): React.ReactElement {
  return (
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
  );
}

function DescriptionShimmer(): React.ReactElement {
  return (
    <div
      className={clsx("flex h-full flex-col justify-between")}
      style={{ gap: "0.5rem", minHeight: "80px" }}
    >
      <div
        className={clsx(
          "h-4 desktop:h-5",
          "bg-black/10 dark:bg-white/10 rounded",
          "w-full",
          "flex-shrink-0"
        )}
      ></div>
      <div
        className={clsx(
          "h-4 desktop:h-5",
          "bg-black/10 dark:bg-white/10 rounded",
          "w-full",
          "flex-shrink-0"
        )}
      ></div>
      <div
        className={clsx(
          "h-4 desktop:h-5",
          "bg-black/10 dark:bg-white/10 rounded",
          "w-full",
          "flex-shrink-0"
        )}
      ></div>
      <div
        className={clsx(
          "h-4 desktop:h-5",
          "bg-black/10 dark:bg-white/10 rounded",
          "w-3/4",
          "flex-shrink-0"
        )}
      ></div>
    </div>
  );
}

interface ServiceArtCoverProps {
  serviceName: ServiceName;
  coverUrl: string | undefined;
  coverType: "image" | "video";
  showShimmer: boolean;
  modalContent: ModalContent;
  onOpenModal: (content: ModalContent) => void;
}

function ServiceArtCover({
  serviceName,
  coverUrl,
  coverType,
  showShimmer,
  modalContent,
  onOpenModal,
}: ServiceArtCoverProps): React.ReactElement {
  if (showShimmer) {
    return <CoverShimmer />;
  }

  return (
    <button
      id={`${serviceName}-cover-link`}
      onClick={() => onOpenModal(modalContent)}
      className={clsx("block w-full cursor-pointer aspect-square")}
      aria-label={`Open ${modalContent.playlistName || modalContent.serviceDisplayName || "playlist"} description`}
      style={{ minHeight: 0 }}
    >
      <MediaSquare
        src={coverUrl!}
        type={coverType}
        alt={`${serviceName} playlist cover`}
      />
    </button>
  );
}

interface ServiceArtTitleProps {
  showShimmer: boolean;
  serviceDisplayName?: string;
  playlistName?: string;
  modalContent: ModalContent;
  onOpenModal: (content: ModalContent) => void;
}

function ServiceArtTitle({
  showShimmer,
  serviceDisplayName,
  playlistName,
  modalContent,
  onOpenModal,
}: ServiceArtTitleProps): React.ReactElement | null {
  if (showShimmer) {
    return <TitleShimmer />;
  }

  if (!serviceDisplayName && !playlistName) {
    return null;
  }

  const hoverTitle =
    serviceDisplayName && playlistName
      ? `${serviceDisplayName}'s ${playlistName}`
      : serviceDisplayName
        ? `${serviceDisplayName}'s`
        : playlistName || undefined;

  return (
    <div className={clsx("w-full")} title={hoverTitle}>
      {serviceDisplayName && (
        <button
          onClick={() => onOpenModal(modalContent)}
          className={clsx(
            "text-sm desktop:text-xl font-bold",
            "text-black dark:text-white",
            "leading-snug desktop:leading-tight",
            "tracking-tight",
            "text-left truncate w-full"
          )}
        >
          {serviceDisplayName}
          's
        </button>
      )}
      {playlistName && (
        <button
          onClick={() => onOpenModal(modalContent)}
          className={clsx(
            "text-xs desktop:text-lg font-semibold",
            "text-black dark:text-white",
            "leading-snug desktop:leading-tight",
            "tracking-tight",
            "mt-0.5 desktop:mt-1",
            "truncate w-full text-left"
          )}
        >
          {playlistName}
        </button>
      )}
    </div>
  );
}

interface ServiceArtDescriptionProps {
  showShimmer: boolean;
  metadata: ServiceMetadata | undefined;
  serviceName: ServiceName;
  playlistName?: string;
  serviceDisplayName?: string;
  onOpenModal: (content: ModalContent) => void;
}

function ServiceArtDescription({
  showShimmer,
  metadata,
  serviceName,
  playlistName,
  serviceDisplayName,
  onOpenModal,
}: ServiceArtDescriptionProps): React.ReactElement {
  if (showShimmer) {
    return <DescriptionShimmer />;
  }

  return (
    <PlaylistDescription
      key={metadata?.description}
      description={metadata?.description}
      serviceName={serviceName}
      playlistName={playlistName}
      serviceDisplayName={serviceDisplayName}
      onOpenModal={(content) =>
        onOpenModal({
          ...content,
          ...(metadata?.href && { playlistUrl: metadata.href }),
        })
      }
      className={clsx("h-full")}
    />
  );
}

export function ServiceArt({
  serviceName,
  onOpenModal,
  isLoading = false,
}: ServiceArtProps): React.ReactElement {
  const metadataRecord: Record<ServiceName, ServiceMetadata> | null =
    useServiceMetadata();
  const metadata = metadataRecord?.[serviceName];
  const coverUrl = metadata?.coverUrl;
  const coverType =
    serviceName === SERVICE.APPLE_MUSIC && coverUrl?.endsWith(".m3u8")
      ? "video"
      : "image";

  const serviceDisplayName = metadata?.serviceDisplayName;
  const playlistName = metadata?.playlistName;

  // Determine if content is ready - show shimmer if loading OR content not ready
  const hasServiceMetadata = !!metadataRecord && !!metadataRecord[serviceName];
  const hasValidCoverUrl =
    coverUrl && typeof coverUrl === "string" && coverUrl.length > 0;
  const hasMetadata = !!metadata;

  // Show shimmer if loading OR if we don't have what we need
  const showCoverShimmer =
    isLoading || !hasServiceMetadata || !hasValidCoverUrl || !hasMetadata;
  const showTitleShimmer =
    isLoading ||
    !hasServiceMetadata ||
    !hasMetadata ||
    (!serviceDisplayName && !playlistName);
  const showDescriptionShimmer =
    isLoading || !hasServiceMetadata || !hasMetadata || !metadata?.description;

  const modalContent = buildModalContent(
    metadata,
    serviceDisplayName,
    playlistName
  );

  return (
    <div
      id={serviceName}
      className={clsx(
        "service w-full rounded-media",
        "border-2 border-gray-300 dark:border-white",
        "p-2 desktop:p-4",
        "bg-transparent",
        "hover:!bg-gray-50 dark:hover:!bg-gray-900",
        "transition-colors"
      )}
    >
      <div className={clsx("mb-2.5 desktop:mb-4")}>
        <ServiceArtCover
          serviceName={serviceName}
          coverUrl={coverUrl}
          coverType={coverType}
          showShimmer={showCoverShimmer}
          modalContent={modalContent}
          onOpenModal={onOpenModal}
        />
      </div>

      <div
        className={clsx(
          "mb-2 desktop:mb-4",
          "min-h-[48px] desktop:min-h-[72px]",
          "flex flex-col justify-center"
        )}
      >
        <ServiceArtTitle
          showShimmer={showTitleShimmer}
          {...(serviceDisplayName && { serviceDisplayName })}
          {...(playlistName && { playlistName })}
          modalContent={modalContent}
          onOpenModal={onOpenModal}
        />
      </div>

      <div
        className={clsx("border-t border-black/20 dark:border-white/30")}
      ></div>

      <div className={clsx("mt-3 desktop:mt-4 h-[80px] desktop:h-[96px]")}>
        <ServiceArtDescription
          showShimmer={showDescriptionShimmer}
          metadata={metadata}
          serviceName={serviceName}
          {...(playlistName && { playlistName })}
          {...(serviceDisplayName && { serviceDisplayName })}
          onOpenModal={onOpenModal}
        />
      </div>
    </div>
  );
}
