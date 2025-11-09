import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "@/v2/App";

const rootElement = document.getElementById("app-v2");

if (!rootElement) {
  throw new Error("Missing root element #app-v2 for v2 entrypoint");
}

const root = createRoot(rootElement);
root.render(<App />);
