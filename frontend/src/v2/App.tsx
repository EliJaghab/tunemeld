import React, { useEffect } from "react";
import { BrowserRouter, useSearchParams } from "react-router-dom";
import { ThemeContextProvider } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/Header";
import { GenreButtons } from "@/v2/components/GenreButtons";
import { ServiceArtSection } from "@/v2/components/ServiceArtSection";
import { GENRE, type GenreValue } from "@/v2/constants";
import Dither from "@/v2/components/Dither";
import { VerticalPadding } from "@/v2/components/VerticalPadding";

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
        <Header />
        <VerticalPadding size="lg" />
        <ServiceArtSection genre={activeGenre} />
        <VerticalPadding size="lg" />
        <GenreButtons />
        <VerticalPadding size="lg" />
      </main>
    </div>
  );
}

function AppWithProviders(): React.ReactElement {
  const activeGenre = useGenreFromUrl();

  return <AppContent activeGenre={activeGenre} />;
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
