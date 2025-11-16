import React, { useEffect } from "react";
import { BrowserRouter, useSearchParams } from "react-router-dom";
import { ThemeContextProvider } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/header/Header";
import { GenreButtons } from "@/v2/components/shared/GenreButtons";
import { VerticalPadding } from "@/v2/components/shared/VerticalPadding";
import { TuneMeldBackground } from "@/v2/components/shared/TuneMeldBackground";
import { ServiceArtSection } from "@/v2/components/service-playlist/ServiceArtSection";
import { TuneMeldPlaylist } from "@/v2/components/playlist/TuneMeldPlaylist/TuneMeldPlaylist";
import { GENRE, type GenreValue } from "@/v2/constants";

function useGenreFromUrl(): GenreValue {
  const [searchParams, setSearchParams] = useSearchParams();
  const genreParam = searchParams.get("genre");
  const validGenre =
    genreParam && Object.values(GENRE).includes(genreParam as GenreValue)
      ? (genreParam as GenreValue)
      : GENRE.POP;

  useEffect(() => {
    if (!genreParam || genreParam !== validGenre) {
      setSearchParams({ genre: validGenre }, { replace: true });
    }
  }, [genreParam, validGenre, setSearchParams]);

  return validGenre;
}

function AppContent({
  activeGenre,
}: {
  activeGenre: GenreValue;
}): React.ReactElement {
  useEffect(() => {
    document.title = "tunemeld";
  }, []);

  return (
    <main className="relative z-10">
      <VerticalPadding size="lg" />
      <Header />
      <VerticalPadding size="lg" />
      <ServiceArtSection genre={activeGenre} />
      <VerticalPadding size="lg" />
      <GenreButtons />
      <VerticalPadding size="lg" />
      <TuneMeldPlaylist genre={activeGenre} />
      <VerticalPadding size="lg" />
    </main>
  );
}

function AppWithProviders(): React.ReactElement {
  const activeGenre = useGenreFromUrl();

  return (
    <div className="relative min-h-screen bg-background px-4 text-text">
      <TuneMeldBackground />
      <AppContent activeGenre={activeGenre} />
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
