import React from "react";
import clsx from "clsx";

interface CloseButtonProps {
  onClick: (e: React.MouseEvent) => void;
  ariaLabel?: string;
  position?: "top-left" | "top-right" | "relative";
  className?: string;
}

export function CloseButton({
  onClick,
  ariaLabel = "Close",
  position = "top-right",
  className = "",
}: CloseButtonProps): React.ReactElement {
  const positionClasses =
    position === "top-left"
      ? "top-4 left-4"
      : position === "top-right"
        ? "top-4 right-4"
        : "";

  return (
    <button
      onClick={onClick}
      className={clsx(
        "w-8 h-8",
        position !== "relative" && "absolute",
        positionClasses,
        "bg-white/60 dark:bg-gray-700/60 backdrop-blur-md",
        "border border-white/20 dark:border-gray-600/20",
        "rounded-full text-lg",
        "text-black dark:text-white",
        "cursor-pointer z-10",
        "flex items-center justify-center",
        "font-mono leading-none",
        "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]",
        "transition-all",
        "hover:bg-white/80 dark:hover:bg-gray-600/80",
        "hover:border-white/30 dark:hover:border-gray-500/30",
        "hover:scale-105",
        "hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_6px_16px_rgba(0,0,0,0.15)]",
        className
      )}
      aria-label={ariaLabel}
    >
      ×
    </button>
  );
}
