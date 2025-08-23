function isLocalDevelopment() {
  return window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
}

export function getDjangoApiBaseUrl() {
  return isLocalDevelopment() ? "http://localhost:8000" : "https://api.tunemeld.com";
}

// Centralized endpoint configuration during migration so we dont break Prod todo remove
export function getAggregatePlaylistEndpoint(genre) {
  return isLocalDevelopment()
    ? `${getDjangoApiBaseUrl()}/aggregate-playlist/${genre}`
    : `${getDjangoApiBaseUrl()}/playlist-data/${genre}`;
}

export function getServicePlaylistEndpoint(genre, service) {
  return isLocalDevelopment()
    ? `${getDjangoApiBaseUrl()}/playlist/${genre}/${service}`
    : `${getDjangoApiBaseUrl()}/service-playlist/${genre}/${service}`;
}

export function getHeaderArtEndpoint(genre) {
  return isLocalDevelopment()
    ? `${getDjangoApiBaseUrl()}/playlist-metadata/${genre}`
    : `${getDjangoApiBaseUrl()}/header-art/${genre}`;
}

export const DJANGO_API_BASE_URL = getDjangoApiBaseUrl();
