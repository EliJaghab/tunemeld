// Legacy Cloudflare Worker API (being phased out)
export const useProdBackend = true;

export function getApiBaseUrl() {
  if (useProdBackend) {
    return "https://tunemeld.com";
  }
  return window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8787"
    : "https://tunemeld.com";
}

export const API_BASE_URL = getApiBaseUrl();

// New Django Backend API on Railway
export const DJANGO_API_BASE_URL = "https://api.tunemeld.com";
