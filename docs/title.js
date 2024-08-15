export function loadTitleContent() {
    return fetch('html/title.html')
      .then(response => response.text())
      .then(data => {
        document.getElementById('title-container').innerHTML = data;
      });
  }
  