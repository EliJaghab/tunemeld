import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import type { Genre, ButtonLabel } from "@/types";

function createElement(tag: string, className?: string): HTMLElement {
  const element = document.createElement(tag);
  if (className) element.className = className;
  return element;
}

export async function loadAndRenderGenreButtons() {
  try {
    const genres = stateManager.getGenres();
    const genreControlsElement = document.getElementById("genre-controls");

    if (!genres || genres.length === 0 || !genreControlsElement) {
      console.error("Unable to load genre buttons");
      return;
    }

    // Preload all genre images first
    const imageUrls = genres.map((g: Genre) => g.iconUrl).filter(Boolean);
    await stateManager.preloadImages(imageUrls);
    stateManager.markLoaded("genreImagesLoaded");

    // Don't clear shimmer yet if initial load
    const hasShimmer = genreControlsElement.querySelector(".shimmer");
    if (!hasShimmer) {
      genreControlsElement.innerHTML = "";
    }

    // Create container for real buttons (hidden initially if shimmer present)
    const realButtonsContainer = hasShimmer
      ? (createElement("div") as HTMLDivElement)
      : genreControlsElement;

    if (hasShimmer) {
      realButtonsContainer.style.display = "none";
      realButtonsContainer.id = "genre-controls-real";
    }

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

      realButtonsContainer.appendChild(button);
    });

    // If we created a hidden container, append it
    if (hasShimmer && realButtonsContainer !== genreControlsElement) {
      genreControlsElement.appendChild(realButtonsContainer);
    }

    // Mark genre buttons as loaded
    stateManager.markLoaded("genreButtonsLoaded");
  } catch (error) {
    console.error("Failed to load genre buttons:", error);
  }
}
