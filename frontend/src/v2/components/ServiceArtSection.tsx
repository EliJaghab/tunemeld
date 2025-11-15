import React, { useState, useEffect } from "react";
import { ServiceArt } from "@/v2/components/ServiceArt";
import { ServiceMetadataProvider } from "@/v2/ServiceMetadataContext";
import { graphqlClient } from "@/services/graphql-client";
import {
  SERVICE,
  type GenreValue,
  type ServiceName,
  type ServiceMetadata,
} from "@/v2/constants";

interface ServiceArtSectionProps {
  genre: GenreValue;
}

export function ServiceArtSection({
  genre,
}: ServiceArtSectionProps): React.ReactElement | null {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [metadata, setMetadata] = useState<Record<
    ServiceName,
    ServiceMetadata
  > | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

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

            newMetadata[serviceName] = metadata;
          }
        });

        setMetadata(newMetadata);
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
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

  if (!metadata) {
    return null;
  }

  return (
    <ServiceMetadataProvider value={metadata}>
      <section className="flex justify-center px-3 desktop:px-4">
        <div className="flex gap-2 justify-center w-full max-w-container desktop:gap-6">
          <ServiceArt serviceName={SERVICE.APPLE_MUSIC} />
          <ServiceArt serviceName={SERVICE.SOUNDCLOUD} />
          <ServiceArt serviceName={SERVICE.SPOTIFY} />
        </div>
      </section>
    </ServiceMetadataProvider>
  );
}
