import { graphqlClient } from "@/services/graphql-client.js";
import { stateManager } from "@/state/StateManager.js";

export async function loadGenresIntoSelector() {
  try {
    const data = await graphqlClient.getAvailableGenres();
    const { genres, defaultGenre } = data;
    const genreSelector = stateManager.getElement("genre-selector");

    if (!genreSelector) {
      throw new Error("Genre selector not found");
    }

    if (!genres || genres.length === 0) {
      throw new Error("No genres available from backend");
    }

    genreSelector.innerHTML = "";

    genres.forEach((genre) => {
      const option = document.createElement("option");
      option.value = genre.name;
      option.textContent = genre.displayName;
      genreSelector.appendChild(option);
    });

    console.log(
      `Loaded ${genres.length} genres from backend:`,
      genres.map((g) => g.name),
    );
    console.log(`Default genre from backend: ${defaultGenre}`);
    return defaultGenre;
  } catch (error) {
    console.error("Failed to load genres from backend:", error);
    throw error;
  }
}
