function isLocalDevelopment() {
  return window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
}

export function getDjangoApiBaseUrl() {
  return isLocalDevelopment() ? "http://localhost:8000" : "https://api.tunemeld.com";
}

export function getAggregatePlaylistEndpoint(genre) {
  return `${getDjangoApiBaseUrl()}/aggregate-playlist/${genre}`;
}

export function getServicePlaylistEndpoint(genre, service) {
  return isLocalDevelopment()
    ? `${getDjangoApiBaseUrl()}/playlist/${genre}/${service}`
    : `${getDjangoApiBaseUrl()}/service-playlist/${genre}/${service}`;
}

export const DJANGO_API_BASE_URL = getDjangoApiBaseUrl();
