import React, { useState, useEffect } from "react";
import { ServiceArt } from "@/v2/components/service-playlist";
import { ServiceMetadataProvider } from "@/v2/ServiceMetadataContext";
import { graphqlClient } from "@/services/graphql-client";
import { ServicePlaylistDescriptionModal } from "@/v2/components/service-playlist";
import {
  SERVICE,
  type GenreValue,
  type ServiceName,
  type ServiceMetadata,
} from "@/v2/constants";

interface ServiceArtSectionProps {
  genre: GenreValue;
}

interface ModalContent {
  serviceDisplayName?: string;
  playlistName?: string;
  description?: string;
}

export function ServiceArtSection({
  genre,
}: ServiceArtSectionProps): React.ReactElement | null {
  const [loading, setLoading] = useState(true);
  const [metadata, setMetadata] = useState<Record<
    ServiceName,
    ServiceMetadata
  > | null>(null);
  const [modalContent, setModalContent] = useState<ModalContent | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setLoading(true);

        const data = await graphqlClient.getPlaylistMetadata(genre);

        if (cancelled) return;

        const newMetadata: Record<ServiceName, ServiceMetadata> = {} as Record<
          ServiceName,
          ServiceMetadata
        >;

        data.playlists.forEach((playlist) => {
          const serviceName = playlist.serviceName as ServiceName;
          if (playlist.playlistUrl) {
            const metadata: ServiceMetadata = {
              href: playlist.playlistUrl,
            };

            if (playlist.playlistCoverDescriptionText) {
              metadata.description = playlist.playlistCoverDescriptionText;
            }

            if (playlist.playlistCoverUrl) {
              metadata.coverUrl = playlist.playlistCoverUrl;
            }

            if (playlist.playlistName) {
              metadata.playlistName = playlist.playlistName;
            }

            if (playlist.serviceDisplayName) {
              metadata.serviceDisplayName = playlist.serviceDisplayName;
            }

            newMetadata[serviceName] = metadata;
          }
        });

        setMetadata(newMetadata);
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to fetch playlist metadata:", err);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
  }, [genre]);

  return (
    <ServiceMetadataProvider
      value={metadata || ({} as Record<ServiceName, ServiceMetadata>)}
    >
      <section className="flex justify-center px-2 desktop:px-4">
        <div className="flex gap-1.5 justify-center w-full max-w-container desktop:gap-6">
          <ServiceArt
            serviceName={SERVICE.APPLE_MUSIC}
            onOpenModal={setModalContent}
            isLoading={loading}
          />
          <ServiceArt
            serviceName={SERVICE.SOUNDCLOUD}
            onOpenModal={setModalContent}
            isLoading={loading}
          />
          <ServiceArt
            serviceName={SERVICE.SPOTIFY}
            onOpenModal={setModalContent}
            isLoading={loading}
          />
        </div>
      </section>

      <ServicePlaylistDescriptionModal
        isOpen={modalContent !== null}
        onClose={() => setModalContent(null)}
      >
        <div className="pr-10">
          {(modalContent?.serviceDisplayName || modalContent?.playlistName) && (
            <div className="mb-3">
              {modalContent?.serviceDisplayName && (
                <h2 className="text-base desktop:text-2xl font-bold text-black dark:text-white">
                  {modalContent.serviceDisplayName}'s
                </h2>
              )}
              {modalContent?.playlistName && (
                <h3 className="text-sm desktop:text-xl font-semibold text-black dark:text-white mt-1">
                  {modalContent.playlistName}
                </h3>
              )}
            </div>
          )}
          <div className="text-sm desktop:text-base text-black dark:text-white leading-6 whitespace-pre-wrap break-words max-h-[60vh] overflow-y-auto py-2">
            {modalContent?.description}
          </div>
        </div>
      </ServicePlaylistDescriptionModal>
    </ServiceMetadataProvider>
  );
}
