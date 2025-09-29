/**
 * Shared Table Structure Configurations
 *
 * This ensures the actual playlist table and shimmer table stay in perfect lockstep.
 * Any changes to table structure must be made here to update both simultaneously.
 */

import { SHIMMER_TYPES, type ShimmerType } from "./constants.js";

interface ColumnConfig {
  name: string;
  className: string;
  hasShimmer: boolean;
  shimmerClass?: string;
  shimmerCount?: number;
}

interface TableStructure {
  columns: ColumnConfig[];
  description: string;
}

type TableStructures = {
  [K in ShimmerType]: TableStructure;
};

export const TABLE_STRUCTURES: TableStructures = {
  [SHIMMER_TYPES.TUNEMELD]: {
    columns: [
      {
        name: "rank",
        className: "rank",
        hasShimmer: true,
        shimmerClass: "shimmer-rank",
      },
      {
        name: "cover",
        className: "cover",
        hasShimmer: true,
        shimmerClass: "shimmer-album-cover",
      },
      {
        name: "info",
        className: "info",
        hasShimmer: true,
        shimmerClass: "shimmer-track-info",
      },
      { name: "spacer", className: "spacer", hasShimmer: false },
      {
        name: "seen-on",
        className: "seen-on",
        hasShimmer: true,
        shimmerClass: "shimmer-source-icons",
        shimmerCount: 3,
      },
    ],
    description:
      "TuneMeld Rank: 5 columns - NO view count columns, NO external links",
  },

  [SHIMMER_TYPES.PLAYCOUNT]: {
    columns: [
      {
        name: "rank",
        className: "rank",
        hasShimmer: true,
        shimmerClass: "shimmer-rank",
      },
      {
        name: "cover",
        className: "cover",
        hasShimmer: true,
        shimmerClass: "shimmer-album-cover",
      },
      {
        name: "info",
        className: "info",
        hasShimmer: true,
        shimmerClass: "shimmer-track-info",
      },
      { name: "spacer", className: "spacer", hasShimmer: false },
      {
        name: "total-play-count",
        className: "total-play-count",
        hasShimmer: true,
        shimmerClass: "shimmer-view-count",
      },
      {
        name: "trending",
        className: "trending",
        hasShimmer: true,
        shimmerClass: "shimmer-view-count",
      },
      {
        name: "seen-on",
        className: "seen-on",
        hasShimmer: true,
        shimmerClass: "shimmer-source-icons",
        shimmerCount: 3,
      },
      {
        name: "external",
        className: "external",
        hasShimmer: true,
        shimmerClass: "shimmer-external-links",
      },
    ],
    description:
      "Play Count Rank: 8 columns - WITH view count columns, WITH external links",
  },
};

/**
 * Creates a shimmer row based on the table structure configuration
 */
export function createShimmerRowFromStructure(
  shimmerType: ShimmerType,
): HTMLTableRowElement | null {
  const structure = TABLE_STRUCTURES[shimmerType];
  if (!structure) {
    console.error(`Unknown shimmer type: ${shimmerType}`);
    return null;
  }

  const row = document.createElement("tr");
  row.className = "playlist-shimmer-row";

  structure.columns.forEach((column, index) => {
    const cell = document.createElement("td");
    cell.className = column.className;

    if (column.hasShimmer) {
      if (column.shimmerCount && column.shimmerClass) {
        // Special case for seen-on with multiple icon shimmers
        const container = document.createElement("div");
        container.className = column.shimmerClass;
        for (let i = 0; i < column.shimmerCount; i++) {
          const shimmer = document.createElement("div");
          shimmer.className = "shimmer shimmer-source-icon";
          container.appendChild(shimmer);
        }
        cell.appendChild(container);
      } else if (column.shimmerClass) {
        // Single shimmer element
        const shimmer = document.createElement("div");
        shimmer.className = `shimmer ${column.shimmerClass || ""}`;
        cell.appendChild(shimmer);
      }
    }

    row.appendChild(cell);
  });

  return row;
}

/**
 * Gets the column structure for a given shimmer type
 */
export function getTableStructure(
  shimmerType: ShimmerType,
): TableStructure | undefined {
  return TABLE_STRUCTURES[shimmerType];
}
