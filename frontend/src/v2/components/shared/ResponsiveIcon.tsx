import React from "react";
import clsx from "clsx";

const ICON_SIZES = {
  xs: {
    base: "h-3 w-3",
    desktop: "desktop:h-3.5 desktop:w-3.5",
  },
  sm: {
    base: "h-3.5 w-3.5",
    desktop: "desktop:h-4 desktop:w-4",
  },
  md: {
    base: "h-4 w-4",
    desktop: "desktop:h-5 desktop:w-5",
  },
  lg: {
    base: "h-5 w-5",
    desktop: "desktop:h-6 desktop:w-6",
  },
  xl: {
    base: "h-6 w-6",
    desktop: "desktop:h-8 desktop:w-8",
  },
} as const;

type IconSize = keyof typeof ICON_SIZES;

interface ResponsiveIconProps
  extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, "height" | "width"> {
  size?: IconSize;
}

export function ResponsiveIcon({
  size = "sm",
  className,
  ...imgProps
}: ResponsiveIconProps): React.ReactElement {
  const sizeClasses = ICON_SIZES[size];

  return (
    <img
      {...imgProps}
      className={clsx(sizeClasses.base, sizeClasses.desktop, className)}
      alt=""
    />
  );
}

export const ICON_SIZE = ICON_SIZES;
