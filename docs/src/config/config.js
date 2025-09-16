export function isLocalDevelopment() {
  return (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname === ""
  );
}

export function applyCacheBusting() {
  if (isLocalDevelopment()) {
    const timestamp = Date.now();

    document.querySelectorAll('link[rel="stylesheet"]').forEach((link) => {
      const href = link.getAttribute("href");
      if (href && !href.includes("http") && !href.includes("?")) {
        link.setAttribute("href", href + "?v=" + timestamp);
      }
    });

    document.querySelectorAll("script[src]").forEach((script) => {
      const src = script.getAttribute("src");
      if (src && !src.includes("http") && !src.includes("?")) {
        script.setAttribute("src", src + "?v=" + timestamp);
      }
    });
  }
}

export function getDjangoApiBaseUrl() {
  return isLocalDevelopment()
    ? "http://localhost:8000"
    : "https://api.tunemeld.com";
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
