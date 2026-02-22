import { useMediaPlayerStore } from "@/v2/stores/useMediaPlayerStore";
import type { GenreValue } from "@/v2/constants";

export function useGenreNavigation() {
  const { genre, handleGenreChange } = useMediaPlayerStore();

  return {
    currentGenre: genre,
    handleGenreChange,
  };
}
