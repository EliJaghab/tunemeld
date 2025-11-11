import React, { useEffect } from "react";
import { ThemeContextProvider } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/Header";
import { ServicePlaylistArt } from "@/v2/components/ServicePlaylistArt";
import { GenreButtons } from "@/v2/components/GenreButtons";
import { ServiceMetadataProvider } from "@/v2/ServiceMetadataContext";
import { ActiveGenreProvider } from "@/v2/ActiveGenreContext";
import { SERVICE } from "@/v2/constants";
import Dither from "@/v2/components/Dither";
import { VerticalPadding } from "@/v2/components/VerticalPadding";

function AppContent(): React.ReactElement {
  useEffect(() => {
    document.title = "tunemeld";
  }, []);

  return (
    <div className="relative min-h-screen bg-background px-4 text-text">
      <Dither
        className="pointer-events-none absolute inset-0 z-0 h-full w-full select-none"
        waveColor={[0.2, 0.2, 0.2]}
        disableAnimation={false}
        enableMouseInteraction={false}
        mouseRadius={0.3}
        colorNum={3}
        waveAmplitude={0.25}
        waveFrequency={2}
        waveSpeed={0.05}
      />
      <main className="relative z-10">
        <VerticalPadding size="lg" />
        <header id="title-container">
          <Header />
        </header>
        <VerticalPadding size="lg" />
        <section className="flex justify-center px-3 desktop:px-4">
          <div className="flex gap-6 justify-center">
            <ServicePlaylistArt serviceName={SERVICE.APPLE_MUSIC} />
            <ServicePlaylistArt serviceName={SERVICE.SOUNDCLOUD} />
            <ServicePlaylistArt serviceName={SERVICE.SPOTIFY} />
          </div>
        </section>
        <VerticalPadding size="lg" />
        <GenreButtons />
        <VerticalPadding size="lg" />
      </main>
    </div>
  );
}

export function App(): React.ReactElement {
  return (
    <ThemeContextProvider>
      <ActiveGenreProvider>
        <ServiceMetadataProvider>
          <AppContent />
        </ServiceMetadataProvider>
      </ActiveGenreProvider>
    </ThemeContextProvider>
  );
}
