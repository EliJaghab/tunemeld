import React from "react";
import GlassSurface from "@/v2/components/GlassSurface";

interface GlassButtonProps {
  onClick?: () => void;
  className?: string;
  children: React.ReactNode;
  active?: boolean;
  ariaLabel?: string;
  type?: "button" | "submit" | "reset";
}

export function GlassButton({
  onClick,
  className = "",
  children,
  active = false,
  ariaLabel,
  type = "button",
}: GlassButtonProps): React.ReactElement {
  return (
    <GlassSurface
      width="auto"
      height="auto"
      borderRadius={50}
      backgroundOpacity={0.1}
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
      className={`cursor-pointer transition-all hover:scale-105 ${
        active ? "outline outline-[1px] outline-white outline-offset-0" : ""
      } ${className}`}
    >
      <button
        type={type}
        onClick={onClick}
        className="flex items-center gap-2 px-4 py-2 text-white desktop:gap-3 desktop:px-6 desktop:py-3"
        aria-label={ariaLabel}
      >
        {children}
      </button>
    </GlassSurface>
  );
}
