import React from "react";
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
      backgroundOpacity={0.05}
      saturation={1}
      borderWidth={0}
      brightness={50}
      opacity={0.93}
      blur={6}
      displace={0.2}
      distortionScale={-180}
      redOffset={0}
      greenOffset={5}
      blueOffset={10}
      className={`cursor-pointer transition-all hover:scale-105 rounded-full ${
        active
          ? "border-2 border-black dark:border-white"
          : "border-2 border-transparent"
      } ${className}`}
    >
      <button
        type={type}
        onClick={onClick}
        className="flex items-center gap-2 px-3 py-1.5 desktop:px-4 desktop:py-2 text-sm desktop:text-base font-medium !text-black dark:!text-white"
        aria-label={ariaLabel}
      >
        {iconUrl && <ResponsiveIcon src={iconUrl} alt="" size="md" />}
        <span>{text}</span>
      </button>
    </GlassSurface>
  );
}
