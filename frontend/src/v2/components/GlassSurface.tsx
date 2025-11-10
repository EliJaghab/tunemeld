import React from "react";
import { cn } from "@/v2/lib/utils";

type GlassSurfaceProps = {
  children: React.ReactNode;
  className?: string;
};

export function GlassSurface({ children, className }: GlassSurfaceProps) {
  return <div className={cn("glass-surface", className)}>{children}</div>;
}
