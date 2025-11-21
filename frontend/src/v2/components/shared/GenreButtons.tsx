import React from "react";
import clsx from "clsx";
import { useSearchParams } from "react-router-dom";
import { FilterButton } from "@/v2/components/shared/FilterButton";
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
    iconUrl: "/images/genre-pop.png",
  },
  {
    name: GENRE.RAP,
    displayName: "Rap",
    iconUrl: "/images/genre-rap.png",
  },
  {
    name: GENRE.DANCE,
    displayName: "Dance",
    iconUrl: "/images/genre-dance.png",
  },
  {
    name: GENRE.COUNTRY,
    displayName: "Country",
    iconUrl: "/images/genre-country.png",
  },
];

export function GenreButtons(): React.ReactElement {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeGenre = searchParams.get("genre") as GenreValue | null;

  const handleGenreClick = (genre: GenreValue) => {
    setSearchParams({
      genre,
    });
  };

  return (
    <div className={clsx("flex justify-center px-3 desktop:px-4")}>
      <div
        className={clsx("flex flex-wrap gap-2 justify-center max-w-container")}
      >
        {GENRES.map((genre) => (
          <FilterButton
            key={genre.name}
            onClick={() => handleGenreClick(genre.name)}
            active={activeGenre === genre.name}
            text={genre.displayName}
            iconUrl={genre.iconUrl}
            ariaLabel={`View ${genre.displayName} playlists`}
          />
        ))}
      </div>
    </div>
  );
}
