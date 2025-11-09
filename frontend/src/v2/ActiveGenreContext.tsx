import React, { createContext, useContext, useState } from "react";
import { GENRE, type GenreValue } from "@/v2/constants";

export const ActiveGenreContext = createContext<
  [GenreValue, (genre: GenreValue) => void]
>([GENRE.POP, () => undefined]);

export function ActiveGenreProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [activeGenre, setActiveGenre] = useState<GenreValue>(GENRE.POP);

  return (
    <ActiveGenreContext.Provider value={[activeGenre, setActiveGenre]}>
      {children}
    </ActiveGenreContext.Provider>
  );
}

export const useActiveGenre = (): [GenreValue, (genre: GenreValue) => void] =>
  useContext(ActiveGenreContext);
