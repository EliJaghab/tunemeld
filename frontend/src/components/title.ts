import { APP_BASE_URL } from "@/config/config";

export function loadTitleContent(): Promise<void> {
  return fetch("html/title.html")
    .then((response: Response) => response.text())
    .then((data: string) => {
      const titleContainer = document.getElementById("title-container");
      if (titleContainer) {
        titleContainer.innerHTML = data;
        const logoTitleLink = titleContainer.querySelector(".logo-title-link");
        if (logoTitleLink) {
          logoTitleLink.setAttribute("href", APP_BASE_URL);
        }
      }
    });
}
