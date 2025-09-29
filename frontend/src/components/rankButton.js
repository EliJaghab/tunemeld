import { graphqlClient } from "@/services/graphql-client.js";
import { sortTable } from "@/components/playlist.js";
import { stateManager } from "@/state/StateManager.js";
import { appRouter } from "@/routing/router.js";

export async function loadAndRenderRankButtons() {
  try {
    const ranks = appRouter.getAvailableRanks();
    const sortControlsElement = document.getElementById("sort-controls");

    if (!ranks || ranks.length === 0 || !sortControlsElement) {
      console.error("Unable to load rank buttons");
      return;
    }

    sortControlsElement.innerHTML = "";

    // Create an array of promises to fetch button labels for each rank
    const buttonPromises = ranks.map(async (rank, index) => {
      const button = document.createElement("button");
      const isCurrentlyActive = stateManager.isRankActive(rank.sortField);
      button.className = isCurrentlyActive
        ? "sort-button active"
        : "sort-button";
      button.setAttribute("data-sort", rank.sortField);
      button.setAttribute("data-order", rank.sortOrder);

      // Fetch button labels for this rank type
      try {
        const buttonLabels = await graphqlClient.getRankButtonLabels(rank.name);
        if (buttonLabels && buttonLabels.length > 0) {
          const rankLabel = buttonLabels.find(
            (label) => label.buttonType === "rank_button",
          );
          if (rankLabel) {
            if (rankLabel.title) {
              button.title = rankLabel.title;
            }
            if (rankLabel.ariaLabel) {
              button.setAttribute("aria-label", rankLabel.ariaLabel);
            }
          }
        }
      } catch (error) {
        console.warn(
          "Failed to load button labels for rank:",
          rank.name,
          error,
        );
        // Continue without labels if fetch fails
      }

      const text = document.createTextNode(rank.displayName);
      button.appendChild(text);

      button.addEventListener("click", function () {
        document
          .querySelectorAll(".sort-controls .sort-button")
          .forEach((btn) => {
            btn.classList.remove("active");
          });
        button.classList.add("active");

        const sortField = rank.sortField;
        const sortOrder = rank.sortOrder;

        stateManager.setCurrentColumn(sortField);
        stateManager.setCurrentOrder(sortOrder);

        appRouter.navigateToRank(rank.sortField);
      });

      return button;
    });

    // Wait for all buttons to be created and then append them
    const buttons = await Promise.all(buttonPromises);
    buttons.forEach((button) => {
      sortControlsElement.appendChild(button);
    });
  } catch (error) {
    console.error("Failed to load rank buttons:", error);
    // No fallback - require backend to be available
  }
}
