import { graphqlClient } from "@/services/graphql-client";
import { stateManager } from "@/state/StateManager";
import { appRouter } from "@/routing/router";
import type { Rank, ButtonLabel } from "@/types/index";

export async function loadAndRenderRankButtons(): Promise<void> {
  try {
    const ranks = appRouter.getAvailableRanks();
    const sortControlsElement = document.getElementById("sort-controls");

    if (!ranks || ranks.length === 0 || !sortControlsElement) {
      console.error("Unable to load rank buttons");
      return;
    }

    // Only clear if we don't already have the correct buttons
    const existingButtons =
      sortControlsElement.querySelectorAll(".sort-button");
    if (existingButtons.length !== ranks.length) {
      sortControlsElement.innerHTML = "";
    } else {
      return; // Don't rebuild if we already have the right buttons
    }

    // Create an array of promises to fetch button labels for each rank
    const buttonPromises = ranks.map(
      async (rank: Rank, index: number): Promise<HTMLButtonElement> => {
        const button = document.createElement("button");
        const isCurrentlyActive = stateManager.isRankActive(rank.sortField);
        button.className = isCurrentlyActive
          ? "sort-button active"
          : "sort-button";
        button.setAttribute("data-sort", rank.sortField);
        button.setAttribute("data-order", rank.sortOrder);

        // Fetch button labels for this rank type
        try {
          const buttonLabels = await graphqlClient.getRankButtonLabels(
            rank.name,
          );
          if (buttonLabels && buttonLabels.length > 0) {
            const rankLabel = buttonLabels.find(
              (label: ButtonLabel) => label.buttonType === "rank_button",
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

        button.addEventListener("click", function (): void {
          document
            .querySelectorAll(".sort-controls .sort-button")
            .forEach((btn: Element) => {
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
      },
    );

    // Wait for all buttons to be created and then append them
    const buttons = await Promise.all(buttonPromises);
    buttons.forEach((button: HTMLButtonElement) => {
      sortControlsElement.appendChild(button);
    });
  } catch (error) {
    console.error("Failed to load rank buttons:", error);
    // No fallback - require backend to be available
  }
}
