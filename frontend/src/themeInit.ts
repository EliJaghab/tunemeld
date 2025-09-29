(function (): void {
  function getTimeBasedTheme(): "dark" | "light" {
    const hour = new Date().getHours();
    return hour >= 19 || hour < 7 ? "dark" : "light";
  }

  const storedTheme: string | null = localStorage.getItem("theme");
  const theme: string = storedTheme || getTimeBasedTheme();

  if (theme === "dark") {
    document.documentElement.classList.add("dark-mode-loading");
  }
})();
