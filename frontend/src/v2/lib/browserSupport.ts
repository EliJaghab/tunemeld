export function supportsBackdropFilter(): boolean {
  if (typeof CSS === "undefined" || !CSS.supports) {
    return false;
  }

  if (CSS.supports("backdrop-filter", "blur(1px)")) {
    return true;
  }

  if (CSS.supports("-webkit-backdrop-filter", "blur(1px)")) {
    return true;
  }

  return false;
}

export function supportsBackdropFilterSVG(filterId?: string): boolean {
  if (!supportsBackdropFilter()) {
    return false;
  }

  const testId = filterId || "test-filter";
  const testValue = `url(#${testId})`;

  try {
    const div = document.createElement("div");
    div.style.backdropFilter = testValue;
    const supports = div.style.backdropFilter !== "";

    if (!supports) {
      const webkitStyle = div.style as CSSStyleDeclaration & {
        webkitBackdropFilter?: string;
      };
      webkitStyle.webkitBackdropFilter = testValue;
      return webkitStyle.webkitBackdropFilter !== "";
    }

    return supports;
  } catch {
    return false;
  }
}

export function isMobileDevice(): boolean {
  if (typeof navigator === "undefined") {
    return false;
  }

  const ua = navigator.userAgent;
  const isIOS = /iPad|iPhone|iPod/.test(ua);
  const isAndroid = /Android/.test(ua);
  const isMobileUA =
    /Mobile|Tablet/.test(ua) ||
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua);
  const hasTouch =
    "ontouchstart" in window || (navigator.maxTouchPoints ?? 0) > 0;

  return isIOS || isAndroid || (isMobileUA && hasTouch);
}

export function isSafari(): boolean {
  if (typeof navigator === "undefined") {
    return false;
  }

  const ua = navigator.userAgent;
  return /Safari/.test(ua) && !/Chrome|CriOS|FxiOS|Chromium|Edg/.test(ua);
}
