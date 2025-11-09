import React, { useEffect } from "react";
import { ThemeContextProvider } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/Header";
import { ServicePlaylistArt } from "@/v2/components/ServicePlaylistArt";
import { ServiceMetadataProvider } from "@/v2/ServiceMetadataContext";
import { ActiveGenreProvider } from "@/v2/ActiveGenreContext";
import { SERVICE } from "@/v2/constants";

export function App(): React.ReactElement {
  useEffect(() => {
    document.title = "tunemeld";
  }, []);

  return (
    <ThemeContextProvider>
      <ActiveGenreProvider>
        <ServiceMetadataProvider>
          <main className="container">
            <header id="title-container">
              <Header />
            </header>
            <section
              id="header-art"
              className="header-art-section"
              aria-label="Featured playlists"
            >
              <ServicePlaylistArt serviceName={SERVICE.APPLE_MUSIC} />
              <ServicePlaylistArt serviceName={SERVICE.SOUNDCLOUD} />
              <ServicePlaylistArt serviceName={SERVICE.SPOTIFY} />
            </section>
          </main>
        </ServiceMetadataProvider>
      </ActiveGenreProvider>
    </ThemeContextProvider>
  );
}
