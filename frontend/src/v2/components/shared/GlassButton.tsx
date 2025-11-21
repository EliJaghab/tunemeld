import React from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";

interface GlassButtonProps {
  onClick?: () => void;
  className?: string;
  buttonClassName?: string;
  children: React.ReactNode;
  active?: boolean;
  ariaLabel?: string;
  type?: "button" | "submit" | "reset";
  borderRadius?: number;
  width?: number | string;
  height?: number | string;
}

export function GlassButton({
  onClick,
  className = "",
  buttonClassName = "",
  children,
  active = false,
  ariaLabel,
  type = "button",
  borderRadius = 50,
  width = "auto",
  height = "auto",
}: GlassButtonProps): React.ReactElement {
  return (
    <GlassSurface
      width={width}
      height={height}
      borderRadius={borderRadius}
      backgroundOpacity={active ? 0 : 0.1}
      borderWidth={0}
      blur={6}
      className={clsx(
        "cursor-pointer transition-all hover:scale-105",
        active && "!bg-brand-teal dark:!bg-bright-blue",
        className
      )}
      style={
        active
          ? {
              backdropFilter: "none",
              WebkitBackdropFilter: "none",
            }
          : {}
      }
    >
      <button
        type={type}
        onClick={onClick}
        className={clsx(
          "flex items-center gap-2",
          buttonClassName || "px-4 py-2 desktop:gap-3 desktop:px-6 desktop:py-3",
          active ? "text-white" : "text-black dark:text-white"
        )}
        aria-label={ariaLabel}
      >
        {children}
      </button>
    </GlassSurface>
  );
}
