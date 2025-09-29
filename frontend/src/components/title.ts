export function loadTitleContent(): Promise<void> {
  return fetch("html/title.html")
    .then((response: Response) => response.text())
    .then((data: string) => {
      const titleContainer = document.getElementById("title-container");
      if (titleContainer) {
        titleContainer.innerHTML = data;
      }
    });
}
