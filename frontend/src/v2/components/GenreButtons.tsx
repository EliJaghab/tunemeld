import React from "react";
import { useSearchParams } from "react-router-dom";
import { GlassButton } from "@/v2/components/GlassButton";
import { ResponsiveIcon } from "@/v2/components/ResponsiveIcon";
import { GENRE, type GenreValue } from "@/v2/constants";

interface GenreButtonData {
  name: GenreValue;
  displayName: string;
  iconUrl: string;
}

const GENRES: GenreButtonData[] = [
  {
    name: GENRE.POP,
    displayName: "Pop",
    iconUrl: "./images/genre-pop.png",
  },
  {
    name: GENRE.RAP,
    displayName: "Rap",
    iconUrl: "./images/genre-rap.png",
  },
  {
    name: GENRE.DANCE,
    displayName: "Dance",
    iconUrl: "./images/genre-dance.png",
  },
  {
    name: GENRE.COUNTRY,
    displayName: "Country",
    iconUrl: "./images/genre-country.png",
  },
];

export function GenreButtons(): React.ReactElement {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeGenre = searchParams.get("genre") as GenreValue | null;

  const handleGenreClick = (genre: GenreValue) => {
    setSearchParams({ genre });
  };

  return (
    <div className="flex justify-center px-3 desktop:px-4">
      <div className="flex flex-wrap gap-2 justify-center max-w-container">
        {GENRES.map((genre) => (
          <GlassButton
            key={genre.name}
            onClick={() => handleGenreClick(genre.name)}
            active={activeGenre === genre.name}
            ariaLabel={`View ${genre.displayName} playlists`}
          >
            <ResponsiveIcon
              src={genre.iconUrl}
              alt={genre.displayName}
              size="xs"
            />
            <span className="text-[0.6875rem] font-medium desktop:text-xs">
              {genre.displayName}
            </span>
          </GlassButton>
        ))}
      </div>
    </div>
  );
}
