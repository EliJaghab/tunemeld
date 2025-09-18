import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";

export async function loadAndRenderGenreButtons() {
  try {
    const genres = appRouter.getAvailableGenres();
    const genreControlsElement = document.getElementById("genre-controls");

    if (!genres || genres.length === 0 || !genreControlsElement) {
      console.error("Unable to load genre buttons");
      return;
    }

    genreControlsElement.innerHTML = "";

    genres.forEach((genre) => {
      const button = document.createElement("button");
      const isCurrentlyActive = appRouter.getCurrentGenre() === genre.name;
      button.className = isCurrentlyActive
        ? "sort-button active"
        : "sort-button";
      button.setAttribute("data-genre", genre.name);
      button.textContent = genre.displayName;

      button.addEventListener("click", function () {
        document
          .querySelectorAll(".genre-controls .sort-button")
          .forEach((btn) => {
            btn.classList.remove("active");
          });
        button.classList.add("active");

        // Preserve current rank when changing genre
        const currentRank = stateManager.getCurrentColumn();
        appRouter.navigateToGenre(genre.name, currentRank);
      });

      genreControlsElement.appendChild(button);
    });
  } catch (error) {
    console.error("Failed to load genre buttons:", error);
  }
}
