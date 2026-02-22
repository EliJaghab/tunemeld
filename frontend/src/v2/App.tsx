import React, { useEffect, useState } from "react";
import clsx from "clsx";
import { BrowserRouter } from "react-router-dom";
import { ThemeContextProvider } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/header/Header";
import { GenreButtons } from "@/v2/components/shared/GenreButtons";
import { VerticalPadding } from "@/v2/components/shared/VerticalPadding";
import { TuneMeldBackground } from "@/v2/components/shared/TuneMeldBackground";
import { ServiceArtSection } from "@/v2/components/service-playlist/ServiceArtSection";
import { TuneMeldPlaylist } from "@/v2/components/playlist/TuneMeldPlaylist/TuneMeldPlaylist";
import { MediaPlayer } from "@/v2/components/media-player/MediaPlayer";
import { useTrackUrlSync } from "@/v2/hooks/useTrackUrl";
import { useGenreNavigation } from "@/v2/hooks/useGenreNavigation";
import { useMediaPlayerStore } from "@/v2/stores/useMediaPlayerStore";
import type { Track } from "@/types";

function AppContent(): React.ReactElement {
  useTrackUrlSync();
  const { currentGenre: activeGenre, handleGenreChange } = useGenreNavigation();
  const { genre, rank, setRank, openTrack, loadFirstTrackForGenre } =
    useMediaPlayerStore();

  useEffect(() => {
    document.title = "tunemeld";
  }, []);

  const handleTracksLoaded = (tracks: Track[]) => {
    loadFirstTrackForGenre(tracks);
  };

  return (
    <AppContentInner
      activeGenre={genre}
      activeRank={rank}
      openTrack={openTrack}
      setRank={setRank}
      setGenre={handleGenreChange}
      onTracksLoaded={handleTracksLoaded}
    />
  );
}

function AppContentInner({
  activeGenre,
  activeRank,
  openTrack,
  setRank,
  setGenre,
  onTracksLoaded,
}: {
  activeGenre: string;
  activeRank: string;
  openTrack: (track: Track) => void;
  setRank: (rank: string) => void;
  setGenre: (genre: string) => void;
  onTracksLoaded: (tracks: Track[]) => void;
}): React.ReactElement {
  return (
    <>
      <main className={clsx("relative z-10")}>
        <VerticalPadding size="lg" />
        <Header />
        <VerticalPadding size="lg" />
        <ServiceArtSection genre={activeGenre} />
        <VerticalPadding size="lg" />
        <GenreButtons activeGenre={activeGenre} onGenreChange={setGenre} />
        <VerticalPadding size="lg" />
        <TuneMeldPlaylist
          genre={activeGenre}
          onTrackClick={(track) => openTrack(track)}
          onTracksLoaded={onTracksLoaded}
          activeRank={activeRank}
          onRankChange={setRank}
        />
        <VerticalPadding size="lg" />
      </main>
      <MediaPlayer />
    </>
  );
}

function AppWithProviders(): React.ReactElement {
  return (
    <div className={clsx("relative min-h-screen bg-background px-4 text-text")}>
      <TuneMeldBackground />
      <AppContent />
    </div>
  );
}

export function App(): React.ReactElement {
  return (
    <BrowserRouter>
      <ThemeContextProvider>
        <AppWithProviders />
      </ThemeContextProvider>
    </BrowserRouter>
  );
}
