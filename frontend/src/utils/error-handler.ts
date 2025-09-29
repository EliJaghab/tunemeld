class ErrorHandler {
  private retryCallback?: () => void;

  showError(message: string, technicalDetails: string | null = null): void {
    console.error("App Error:", message, technicalDetails);

    const existingBanner = document.getElementById("error-banner");
    if (existingBanner) {
      existingBanner.remove();
    }

    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      const errorBanner = document.createElement("div");
      errorBanner.id = "error-banner";
      errorBanner.className = "error-banner";

      const detailsSection = technicalDetails
        ? `
        <details class="error-banner-details">
          <summary> Technical Details</summary>
          <div class="error-banner-technical">${technicalDetails}</div>
        </details>
      `
        : "";

      errorBanner.innerHTML = `
        <div class="error-banner-content">
          <div class="error-banner-message">
            <div class="error-banner-title"> Service Temporarily Unavailable</div>
            <div class="error-banner-description">${message}</div>
            ${detailsSection}
          </div>
          <button id="error-retry-btn" class="error-banner-retry"> RETRY</button>
        </div>
      `;

      mainContent.insertBefore(errorBanner, mainContent.firstChild);

      const retryBtn = errorBanner.querySelector(
        "#error-retry-btn",
      ) as HTMLButtonElement;
      if (retryBtn && this.retryCallback) {
        retryBtn.title = "Retry loading the page";
        retryBtn.setAttribute("aria-label", "Retry loading the page");

        retryBtn.onclick = (): void => {
          errorBanner.remove();
          this.retryCallback!();
        };
      }
    }
  }

  setRetryCallback(callback: () => void): void {
    this.retryCallback = callback;
  }
}

export const errorHandler = new ErrorHandler();
