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

    ranks.forEach((rank, index) => {
      const button = document.createElement("button");
      const isCurrentlyActive = stateManager.isRankActive(rank.sortField);
      button.className = isCurrentlyActive
        ? "sort-button active"
        : "sort-button";
      button.setAttribute("data-sort", rank.sortField);
      button.setAttribute("data-order", rank.sortOrder);

      const icon = document.createElement("img");
      icon.src = rank.iconUrl;
      icon.alt = rank.displayName;
      icon.className = "button-icon";
      button.appendChild(icon);

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

      sortControlsElement.appendChild(button);
    });
  } catch (error) {
    console.error("Failed to load rank buttons:", error);
    // No fallback - require backend to be available
  }
}
