import React, { useContext, useEffect } from "react";
import { ThemeContextProvider, ThemeContext } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/Header";
import { ServicePlaylistArt } from "@/v2/components/ServicePlaylistArt";
import { ServiceMetadataProvider } from "@/v2/ServiceMetadataContext";
import { ActiveGenreProvider } from "@/v2/ActiveGenreContext";
import { SERVICE, THEME } from "@/v2/constants";
import Dither from "@/v2/components/Dither";
import GlassSurface from "@/v2/components/GlassSurface";

function AppContent(): React.ReactElement {
  const [theme] = useContext(ThemeContext);
  const isDark = theme === THEME.DARK;
  const waveColor: [number, number, number] = isDark
    ? [0.5, 0.5, 0.5]
    : [1, 1, 1];

  useEffect(() => {
    document.title = "tunemeld";
  }, []);

  return (
    <div className="relative min-h-screen bg-background px-4 text-text">
      <Dither
        className="pointer-events-none absolute inset-0 z-0 h-full w-full select-none"
        waveColor={waveColor}
        disableAnimation={false}
        enableMouseInteraction={false}
        mouseRadius={0}
        colorNum={3}
        waveAmplitude={0.1}
        waveFrequency={1.5}
        waveSpeed={0.05}
      />
      <main className="relative z-10">
        <header id="title-container">
          <Header />
        </header>
        <div className="flex justify-center px-3 pb-4 desktop:px-4 desktop:pb-6">
          <GlassSurface
            width="100%"
            height="auto"
            borderRadius={50}
            backgroundOpacity={0.1}
            saturation={1}
            borderWidth={0.07}
            brightness={50}
            opacity={0.93}
            blur={5}
            displace={0.3}
            distortionScale={-180}
            redOffset={0}
            greenOffset={10}
            blueOffset={20}
            className="w-full max-w-container p-8"
          >
            <div className="flex gap-6 justify-center">
              <ServicePlaylistArt serviceName={SERVICE.APPLE_MUSIC} />
              <ServicePlaylistArt serviceName={SERVICE.SOUNDCLOUD} />
              <ServicePlaylistArt serviceName={SERVICE.SPOTIFY} />
            </div>
          </GlassSurface>
        </div>
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
