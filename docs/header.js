import { displayPlaylistMetadata } from "./playlist-metadata.js";

export function showSkeletonLoaders() {
  document.querySelectorAll(".skeleton, .skeleton-text").forEach((el) => {
    el.classList.add("loading");
  });
}

export function hideSkeletonLoaders() {
  document.querySelectorAll(".skeleton, .skeleton-text").forEach((el) => {
    el.classList.remove("loading");
    el.classList.remove("skeleton");
    el.classList.remove("skeleton-text");
  });
}

export async function fetchAndDisplayHeaderArt(genre) {
  await displayPlaylistMetadata(genre);
}
