import { stateManager } from "@/state/StateManager";
import { debugLog } from "@/config/config";
import { appRouter } from "@/routing/router";
import { TUNEMELD_RANK_FIELD } from "@/config/constants";
import type { Rank } from "@/types/index";

const RANK_LOG_PREFIX = "[RankButtons]";
const rankDebug = (message: string, meta?: unknown) => {
  debugLog("RankButtons", message, meta);
};

function createElement(tag: string, className?: string): HTMLElement {
  const element = document.createElement(tag);
  if (className) element.className = className;
  return element;
}

export async function loadAndRenderRankButtons(): Promise<void> {
  try {
    const ranks = stateManager.getRanks();
    const sortControlsElement = document.getElementById("sort-controls");

    if (!ranks || ranks.length === 0 || !sortControlsElement) {
      console.error("Unable to load rank buttons");
      return;
    }

    rankDebug("loadAndRenderRankButtons:start", {
      rankCount: ranks.length,
      hasShimmer: !!sortControlsElement.querySelector(".shimmer"),
    });

    // Check if we have shimmer
    const hasShimmer = sortControlsElement.querySelector(".shimmer");
    const existingRealButtons = sortControlsElement.querySelectorAll(
      ".sort-button:not(.shimmer)",
    );

    if (!hasShimmer && existingRealButtons.length === ranks.length) {
      // Update active states on existing buttons to match current rank
      existingRealButtons.forEach((button: Element) => {
        const sortField = button.getAttribute("data-sort");
        if (sortField) {
          const isActive = stateManager.isRankActive(sortField);
          button.classList.toggle("active", isActive);
        }
      });
      return; // Don't rebuild if we already have the right buttons
    }

    // Create container for real buttons (hidden initially if shimmer present)
    let realButtonsContainer: HTMLElement;

    if (hasShimmer) {
      const existingContainer = document.getElementById(
        "sort-controls-real",
      ) as HTMLElement | null;
      if (existingContainer) {
        realButtonsContainer = existingContainer;
        realButtonsContainer.innerHTML = "";
        rankDebug("Reusing existing real buttons container");
      } else {
        realButtonsContainer = createElement("div");
        realButtonsContainer.id = "sort-controls-real";
        rankDebug("Creating new real buttons container");
      }
      realButtonsContainer.style.display = "none";
    } else {
      const existingContainer = document.getElementById("sort-controls-real");
      if (existingContainer && existingContainer !== sortControlsElement) {
        existingContainer.remove();
      }
      realButtonsContainer = sortControlsElement;
      sortControlsElement.innerHTML = "";
    }

    ranks.forEach((rank: Rank) => {
      if (!rank.displayName) {
        console.error("Missing displayName for rank:", rank);
        throw new Error(`Rank missing required displayName: ${rank.sortField}`);
      }

      const isCurrentlyActive = stateManager.isRankActive(rank.sortField);
      const className = isCurrentlyActive
        ? "sort-button active"
        : "sort-button";

      const button = document.createElement("button");
      button.className = className;
      button.setAttribute("data-sort", rank.sortField);
      button.setAttribute("data-order", rank.sortOrder);
      button.title = `Sort by ${rank.displayName}`;
      button.setAttribute("aria-label", `Sort tracks by ${rank.displayName}`);
      button.textContent = rank.displayName;

      button.addEventListener("click", function (): void {
        document
          .querySelectorAll(".sort-controls .sort-button")
          .forEach((btn: Element) => {
            btn.classList.remove("active");
          });
        button.classList.add("active");

        stateManager.setShimmerTypeFromSortField(rank.sortField);
        appRouter.navigateToRank(rank.sortField);
      });

      realButtonsContainer.appendChild(button);
    });

    // If we created a hidden container, append it when not already attached
    if (hasShimmer && !realButtonsContainer.isConnected) {
      sortControlsElement.appendChild(realButtonsContainer);
    }

    // Mark rank buttons as loaded
    stateManager.markLoaded("rankButtonsLoaded");
    rankDebug("loadAndRenderRankButtons:end");
  } catch (error) {
    console.error("Failed to load rank buttons:", error);
    // No fallback - require backend to be available
  }
}
