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
import { useAppRouting } from "@/v2/hooks/useAppRouting";
import type { Track } from "@/types";

function AppContent(): React.ReactElement {
  const [playlistTracks, setPlaylistTracks] = useState<Track[]>([]);

  const {
    genre: activeGenre,
    rank: activeRank,
    selectedTrack,
    isMediaPlayerOpen,
    openTrack,
    closeMediaPlayer,
    setPlayer,
    setRank,
    setGenre,
  } = useAppRouting(playlistTracks);

  useEffect(() => {
    document.title = "tunemeld";
  }, []);

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
          onTrackClick={(track) => openTrack(track, playlistTracks)}
          onTracksLoaded={setPlaylistTracks}
          activeRank={activeRank}
          onRankChange={setRank}
        />
        <VerticalPadding size="lg" />
      </main>
      <MediaPlayer
        track={selectedTrack}
        isOpen={isMediaPlayerOpen}
        onClose={closeMediaPlayer}
        onServiceClick={setPlayer}
      />
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
