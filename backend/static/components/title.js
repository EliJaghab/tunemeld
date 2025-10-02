export function loadTitleContent() {
  return fetch("html/title.html")
    .then((response) => response.text())
    .then((data) => {
      const titleContainer = document.getElementById("title-container");
      if (titleContainer) {
        titleContainer.innerHTML = data;
      }
    });
}
