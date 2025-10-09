function isPrivateNetworkHost(hostname: string): boolean {
  if (!hostname) return true;

  // Common local development hostnames
  const normalizedHost = hostname.toLowerCase();
  if (
    normalizedHost === "localhost" ||
    normalizedHost === "127.0.0.1" ||
    normalizedHost === "0.0.0.0" ||
    normalizedHost === "::1"
  ) {
    return true;
  }

  // Treat *.local and *.lan domains as local network shortcuts
  if (normalizedHost.endsWith(".local") || normalizedHost.endsWith(".lan")) {
    return true;
  }

  // Private IPv4 ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x
  if (/^10\./.test(normalizedHost)) return true;
  if (/^192\.168\./.test(normalizedHost)) return true;
  if (/^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(normalizedHost)) return true;

  // Link-local IPv6 addresses (e.g., fe80::)
  if (normalizedHost.startsWith("fe80::")) {
    return true;
  }

  return false;
}

export function isLocalDevelopment(): boolean {
  return isPrivateNetworkHost(window.location.hostname);
}

export function applyCacheBusting(): void {
  if (isLocalDevelopment()) {
    const timestamp = Date.now();

    document.querySelectorAll('link[rel="stylesheet"]').forEach((link) => {
      const href = link.getAttribute("href");
      if (href && !href.includes("http")) {
        // Remove existing query params and add new timestamp
        const baseHref = href.split("?")[0];
        link.setAttribute("href", baseHref + "?v=" + timestamp);
      }
    });

    document.querySelectorAll("script[src]").forEach((script) => {
      const src = script.getAttribute("src");
      if (src && !src.includes("http")) {
        // Remove existing query params and add new timestamp
        const baseSrc = src.split("?")[0];
        script.setAttribute("src", baseSrc + "?v=" + timestamp);
      }
    });
  }
}

export function getDjangoApiBaseUrl(): string {
  return isLocalDevelopment()
    ? "http://localhost:8000"
    : "https://api.tunemeld.com";
}

export const DJANGO_API_BASE_URL = getDjangoApiBaseUrl();

export const DEBUG_LOG_ENABLED = isLocalDevelopment();

export function debugLog(
  namespace: string,
  message: string,
  meta?: unknown,
): void {
  if (!DEBUG_LOG_ENABLED) return;
  if (meta === undefined) {
    console.debug(`[${namespace}]`, message);
  } else {
    console.debug(`[${namespace}]`, message, meta);
  }
}
