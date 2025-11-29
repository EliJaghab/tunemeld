import type { Preview } from "@storybook/react-vite";
import React from "react";
import "../src/v2/styles/tailwind.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },

    a11y: {
      // 'todo' - show a11y violations in the test UI only
      // 'error' - fail CI on a11y violations
      // 'off' - skip a11y checks entirely
      test: "todo",
    },

    backgrounds: {
      default: "light",
      values: [
        { name: "light", value: "#f0f0f0" },
        { name: "dark", value: "#1a1a1a" },
        { name: "white", value: "#ffffff" },
      ],
    },
  },

  globalTypes: {
    darkMode: {
      description: "Global dark mode for components",
      defaultValue: "light",
      toolbar: {
        title: "Theme",
        icon: "circlehollow",
        items: [
          { value: "light", icon: "circlehollow", title: "Light" },
          { value: "dark", icon: "circle", title: "Dark" },
        ],
        dynamicTitle: true,
      },
    },
  },

  decorators: [
    (Story, context) => {
      const darkMode = context.globals.darkMode;
      return (
        <div className={darkMode === "dark" ? "dark" : ""}>
          <Story />
        </div>
      );
    },
  ],
};

export default preview;
