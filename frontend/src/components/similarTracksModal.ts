import { graphqlClient } from "@/services/graphql-client";
import { openPlayer } from "@/components/servicePlayer";
import { SERVICE_NAMES } from "@/config/constants";
import { appRouter } from "@/routing/router";
import { stateManager } from "@/state/StateManager";
import type { Track } from "@/types/index";

let modalInitialized = false;

function getPreferredTrackUrl(
  track: Track,
): { url: string; service: string } | null {
  if (track.youtubeUrl) {
    return { url: track.youtubeUrl, service: SERVICE_NAMES.YOUTUBE };
  }
  if (track.soundcloudUrl) {
    return { url: track.soundcloudUrl, service: SERVICE_NAMES.SOUNDCLOUD };
  }
  if (track.spotifyUrl) {
    return { url: track.spotifyUrl, service: SERVICE_NAMES.SPOTIFY };
  }
  if (track.appleMusicUrl) {
    return { url: track.appleMusicUrl, service: SERVICE_NAMES.APPLE_MUSIC };
  }
  return null;
}

export function initSimilarTracksModal(): void {
  if (modalInitialized) {
    return;
  }

  const body = document.body;
  if (!body) {
    console.error("Body element not found.");
    return;
  }

  const overlay = document.createElement("div");
  overlay.className = "modal-overlay-base similar-tracks-overlay";
  overlay.id = "similar-tracks-overlay";

  const modal = document.createElement("div");
  modal.className = "modal-base similar-tracks-modal";
  modal.id = "similar-tracks-modal";

  const closeButton = document.createElement("button");
  closeButton.className = "modal-close-base similar-tracks-modal-close";
  closeButton.innerHTML = "×";
  closeButton.title = "Close";
  closeButton.setAttribute("aria-label", "Close similar tracks");
  closeButton.addEventListener("click", closeSimilarTracksModal);

  const modalHeader = document.createElement("div");
  modalHeader.className = "modal-header-base similar-tracks-modal-header";
  modalHeader.id = "similar-tracks-modal-header";
  modalHeader.textContent = "More Like This";

  const modalContent = document.createElement("div");
  modalContent.className = "similar-tracks-modal-content";
  modalContent.id = "similar-tracks-modal-content";

  modal.appendChild(closeButton);
  modal.appendChild(modalHeader);
  modal.appendChild(modalContent);

  body.appendChild(overlay);
  body.appendChild(modal);

  overlay.addEventListener("click", closeSimilarTracksModal);

  modalInitialized = true;
}

export async function openSimilarTracksModal(
  currentTrack: Track,
): Promise<void> {
  if (!modalInitialized) {
    initSimilarTracksModal();
  }

  const overlay = document.getElementById("similar-tracks-overlay");
  const modal = document.getElementById("similar-tracks-modal");
  const content = document.getElementById("similar-tracks-modal-content");
  const header = document.getElementById("similar-tracks-modal-header");

  if (!overlay || !modal || !content || !header) {
    console.error("Modal elements not found");
    return;
  }

  header.innerHTML = "";

  const moreLikeText = document.createTextNode("More like ");
  header.appendChild(moreLikeText);

  const trackLink = document.createElement("span");
  trackLink.textContent = `${currentTrack.trackName} - ${currentTrack.artistName}`;
  trackLink.style.cursor = "pointer";
  trackLink.title = "Return to track";
  trackLink.className = "similar-tracks-modal-track-link";

  trackLink.addEventListener("click", () => {
    closeSimilarTracksModal();
  });

  header.appendChild(trackLink);

  content.innerHTML = '<div class="similar-tracks-loading">Loading...</div>';

  overlay.classList.add("active");
  modal.classList.add("active");

  try {
    const similarTracks = await graphqlClient.getSimilarTracks(
      currentTrack.isrc,
      10,
    );

    if (similarTracks.length === 0) {
      content.innerHTML = `<div class="similar-tracks-empty">No audio features available for "${currentTrack.trackName}" by ${currentTrack.artistName}</div>`;
      return;
    }

    content.innerHTML = "";

    const trackList = document.createElement("div");
    trackList.className = "similar-tracks-list";

    similarTracks.forEach((track) => {
      const trackItem = document.createElement("div");
      trackItem.className = "similar-track-item";

      const albumArt = document.createElement("img");
      albumArt.className = "similar-track-album-art";
      albumArt.src = track.albumCoverUrl || "/images/placeholder-album.png";
      albumArt.alt = `${track.trackName} album cover`;
      albumArt.loading = "lazy";

      const trackInfo = document.createElement("div");
      trackInfo.className = "similar-track-info";

      const trackName = document.createElement("div");
      trackName.className = "similar-track-name";
      trackName.textContent = track.trackName;

      const artistName = document.createElement("div");
      artistName.className = "similar-track-artist";
      artistName.textContent = track.artistName;

      trackInfo.appendChild(trackName);
      trackInfo.appendChild(artistName);

      const playButtonContainer = document.createElement("div");
      playButtonContainer.className = "similar-track-play-container";

      const trackUrlInfo = getPreferredTrackUrl(track);

      if (trackUrlInfo) {
        const playButton = document.createElement("button");
        playButton.className = "similar-track-play-button";
        playButton.title = "Play track";
        playButton.setAttribute("aria-label", `Play ${track.trackName}`);
        playButton.innerHTML = "▶";

        playButton.addEventListener("click", async () => {
          const currentGenre = appRouter.getCurrentGenre();
          const currentRank = stateManager.getCurrentColumn();

          if (currentGenre) {
            await openPlayer(trackUrlInfo.url, trackUrlInfo.service, track);

            appRouter.updateUrlOnly(
              currentGenre,
              currentRank,
              trackUrlInfo.service,
              track.isrc,
            );
          }

          window.scrollTo({ top: 0, behavior: "smooth" });
        });

        playButtonContainer.appendChild(playButton);
      }

      trackItem.appendChild(albumArt);
      trackItem.appendChild(trackInfo);
      trackItem.appendChild(playButtonContainer);

      trackList.appendChild(trackItem);
    });

    content.appendChild(trackList);
  } catch (error) {
    console.error("Error loading similar tracks:", error);
    content.innerHTML = `<div class="similar-tracks-error">Failed to load similar tracks for "${currentTrack.trackName}" by ${currentTrack.artistName}. This track may not have audio features yet.</div>`;
  }
}

export function closeSimilarTracksModal(): void {
  const overlay = document.getElementById("similar-tracks-overlay");
  const modal = document.getElementById("similar-tracks-modal");

  if (overlay) overlay.classList.remove("active");
  if (modal) modal.classList.remove("active");
}
