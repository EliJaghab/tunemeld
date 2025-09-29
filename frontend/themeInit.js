// Immediate theme detection and application to prevent FOUC
(function () {
  function getTimeBasedTheme() {
    const hour = new Date().getHours();
    return hour >= 19 || hour < 7 ? "dark" : "light";
  }

  const storedTheme = localStorage.getItem("theme");
  const theme = storedTheme || getTimeBasedTheme();

  if (theme === "dark") {
    document.documentElement.classList.add("dark-mode-loading");
  }
})();
