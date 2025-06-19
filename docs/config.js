// Import centralized configuration
import genresConfig from "../config/shared/genres.json";
import servicesConfig from "../config/shared/services.json";
import playlistsConfig from "../config/shared/playlists.json";
import constantsConfig from "../config/shared/constants.json";

// Determine environment
const isProduction = window.location.hostname === "tunemeld.com" || window.location.hostname === "www.tunemeld.com";
const isDevelopment = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";

// Load environment config
let envConfig;
if (isProduction) {
  envConfig = {
    api: {
      django: { baseUrl: "https://api.tunemeld.com" },
      cloudflare: { baseUrl: "https://tunemeld.com" },
    },
    features: { useProdBackend: true },
  };
} else {
  envConfig = {
    api: {
      django: { baseUrl: "https://api.tunemeld.com" },
      cloudflare: { baseUrl: isDevelopment ? "http://127.0.0.1:8787" : "https://tunemeld.com" },
    },
    features: { useProdBackend: true },
  };
}

export const useProdBackend = envConfig.features.useProdBackend;

export function getApiBaseUrl() {
  return envConfig.api.cloudflare.baseUrl;
}

export const API_BASE_URL = getApiBaseUrl();
export const DJANGO_API_BASE_URL = envConfig.api.django.baseUrl;

// Export centralized config objects
export const GENRES = genresConfig.genres;
export const SERVICES = servicesConfig.services;
export const PLAYLISTS = playlistsConfig.playlists;
export const CONSTANTS = constantsConfig;
