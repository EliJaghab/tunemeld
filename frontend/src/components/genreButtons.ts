import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import type { Genre, ButtonLabel } from "@/types";

export async function loadAndRenderGenreButtons() {
  try {
    const genres = stateManager.getGenres();
    const genreControlsElement = document.getElementById("genre-controls");

    if (!genres || genres.length === 0 || !genreControlsElement) {
      console.error("Unable to load genre buttons");
      return;
    }

    genreControlsElement.innerHTML = "";

    genres.forEach((genre: Genre) => {
      const button = document.createElement("button");
      const isCurrentlyActive = appRouter.getCurrentGenre() === genre.name;
      button.className = isCurrentlyActive
        ? "sort-button active"
        : "sort-button";
      button.setAttribute("data-genre", genre.name);

      if (genre.buttonLabels && genre.buttonLabels.length > 0) {
        const genreLabel = genre.buttonLabels.find(
          (label: ButtonLabel) => label.buttonType === "genre_button",
        );
        if (genreLabel) {
          if (genreLabel.title) {
            button.title = genreLabel.title;
          }
          if (genreLabel.ariaLabel) {
            button.setAttribute("aria-label", genreLabel.ariaLabel);
          }
        }
      }

      const icon = document.createElement("img");
      icon.src = genre.iconUrl;
      icon.alt = genre.displayName;
      icon.className = "button-icon";
      button.appendChild(icon);

      const text = document.createTextNode(genre.displayName);
      button.appendChild(text);

      button.addEventListener("click", function () {
        document
          .querySelectorAll(".genre-controls .sort-button")
          .forEach((btn) => {
            btn.classList.remove("active");
          });
        button.classList.add("active");

        // Preserve current rank when changing genre
        const currentRank = stateManager.getCurrentColumn();
        appRouter.navigateToGenre(genre.name, currentRank || null);
      });

      genreControlsElement.appendChild(button);
    });
  } catch (error) {
    console.error("Failed to load genre buttons:", error);
  }
}
