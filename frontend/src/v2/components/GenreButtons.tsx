import React from "react";
import { GlassButton } from "@/v2/components/GlassButton";
import { ResponsiveIcon } from "@/v2/components/ResponsiveIcon";

interface GenreButtonData {
  name: string;
  displayName: string;
  iconUrl: string;
}

const GENRES: GenreButtonData[] = [
  {
    name: "pop",
    displayName: "Pop",
    iconUrl: "./images/genre-pop.png",
  },
  {
    name: "rap",
    displayName: "Rap",
    iconUrl: "./images/genre-rap.png",
  },
  {
    name: "dance",
    displayName: "Dance",
    iconUrl: "./images/genre-dance.png",
  },
  {
    name: "country",
    displayName: "Country",
    iconUrl: "./images/genre-country.png",
  },
];

export function GenreButtons(): React.ReactElement {
  const [activeGenre, setActiveGenre] = React.useState<string>("pop");

  return (
    <div className="flex justify-center px-3 desktop:px-4">
      <div className="flex flex-wrap gap-2 justify-center max-w-container">
        {GENRES.map((genre) => (
          <GlassButton
            key={genre.name}
            onClick={() => setActiveGenre(genre.name)}
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
