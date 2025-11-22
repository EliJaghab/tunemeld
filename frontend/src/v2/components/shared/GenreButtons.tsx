import React from "react";
import clsx from "clsx";
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

interface GenreButtonsProps {
  activeGenre: GenreValue;
  onGenreChange: (genre: GenreValue) => void;
}

export function GenreButtons({
  activeGenre,
  onGenreChange,
}: GenreButtonsProps): React.ReactElement {
  return (
    <div className={clsx("flex justify-center px-3 desktop:px-4")}>
      <div
        className={clsx("flex flex-wrap gap-2 justify-center max-w-container")}
      >
        {GENRES.map((genre) => (
          <FilterButton
            key={genre.name}
            onClick={() => onGenreChange(genre.name)}
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
