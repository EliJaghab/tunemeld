import React from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { ResponsiveIcon } from "@/v2/components/shared/ResponsiveIcon";

interface FilterButtonProps {
  onClick?: () => void;
  className?: string;
  text: string;
  iconUrl?: string;
  active?: boolean;
  ariaLabel?: string;
  type?: "button" | "submit" | "reset";
}

export function FilterButton({
  onClick,
  className = "",
  text,
  iconUrl,
  active = false,
  ariaLabel,
  type = "button",
}: FilterButtonProps): React.ReactElement {
  return (
    <GlassSurface
      width="auto"
      height="auto"
      borderRadius={50}
      backgroundOpacity={active ? 0 : 0.05}
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
          "px-3 py-2 desktop:px-4 desktop:py-2",
          "text-sm desktop:text-base font-medium",
          active ? "!text-white" : "!text-black dark:!text-white"
        )}
        aria-label={ariaLabel}
      >
        {iconUrl && <ResponsiveIcon src={iconUrl} alt="" size="md" />}
        <span>{text}</span>
      </button>
    </GlassSurface>
  );
}
