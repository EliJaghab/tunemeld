import React, { useEffect } from "react";
import { ThemeContextProvider } from "@/v2/ThemeContext";
import { Header } from "@/v2/components/Header";

export function App(): React.ReactElement {
  useEffect(() => {
    document.title = "tunemeld";
  }, []);

  return (
    <ThemeContextProvider>
      <main className="container">
        <header id="title-container">
          <Header />
        </header>
      </main>
    </ThemeContextProvider>
  );
}
