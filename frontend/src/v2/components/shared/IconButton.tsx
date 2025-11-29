import React from "react";
import clsx from "clsx";

interface IconButtonProps {
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  onMouseDown?: (e: React.MouseEvent<HTMLButtonElement>) => void;
  onTouchStart?: (e: React.TouchEvent<HTMLButtonElement>) => void;
  ariaLabel?: string;
  className?: string;
  iconClassName?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "transparent" | "glass" | "glass-container";
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
  padding?: string;
  containerPadding?: string;
  borderRadius?: string | number;
  height?: string | number;
  width?: string | number;
}

const sizeClasses = {
  sm: "w-6 h-6 desktop:w-[30px] desktop:h-[30px]",
  md: "w-8 h-8 desktop:w-10 desktop:h-10",
  lg: "w-10 h-10 desktop:w-12 desktop:h-12",
};

const iconSizeClasses = {
  sm: "w-3.5 h-3.5 desktop:w-4 desktop:h-4",
  md: "w-4 h-4 desktop:w-5 desktop:h-5",
  lg: "w-5 h-5 desktop:w-6 desktop:h-6",
};

const variantClasses = {
  default:
    "bg-white/60 dark:bg-gray-700/60 hover:bg-white/80 dark:hover:bg-gray-600/80 text-black dark:text-white",
  transparent: "bg-transparent hover:opacity-80 text-black dark:text-white",
  glass:
    "bg-black/10 dark:bg-white/10 hover:scale-110 dark:hover:bg-white/20 text-black dark:text-white",
  "glass-container":
    "bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)] text-black dark:text-white",
};

export function IconButton({
  onClick,
  onMouseDown,
  onTouchStart,
  ariaLabel,
  className = "",
  iconClassName = "",
  children,
  size = "sm",
  variant = "default",
  disabled = false,
  type = "button",
  padding,
  containerPadding,
  borderRadius,
  height,
  width,
}: IconButtonProps): React.ReactElement {
  const isGlassContainer = variant === "glass-container";

  const paddingClasses = padding
    ? padding
    : isGlassContainer
      ? containerPadding || "p-2 desktop:p-2.5"
      : "p-0";

  let borderRadiusClasses = "";
  let borderRadiusStyle: React.CSSProperties = {};

  if (borderRadius !== undefined) {
    if (typeof borderRadius === "string") {
      borderRadiusClasses = borderRadius;
    } else {
      borderRadiusStyle.borderRadius = `${borderRadius}px`;
    }
  } else {
    if (isGlassContainer) {
      borderRadiusClasses = "rounded-2xl";
    } else {
      borderRadiusClasses = "rounded-full";
    }
  }

  let widthClasses = "";
  let heightClasses = "";
  let dimensionStyle: React.CSSProperties = {};

  if (height !== undefined) {
    if (typeof height === "string") {
      heightClasses = height;
      widthClasses = height.replace("h-", "w-");
    } else {
      dimensionStyle.height = `${height}px`;
      dimensionStyle.width = `${height}px`;
    }
  } else if (width !== undefined) {
    if (typeof width === "string") {
      widthClasses = width;
    } else {
      dimensionStyle.width = `${width}px`;
    }
  }

  return (
    <button
      type={type}
      onClick={onClick}
      onMouseDown={onMouseDown}
      onTouchStart={onTouchStart}
      aria-label={ariaLabel}
      disabled={disabled}
      className={clsx(
        !isGlassContainer && !height && !width && sizeClasses[size],
        widthClasses,
        heightClasses,
        borderRadiusClasses,
        "flex items-center justify-center",
        "flex-shrink-0",
        !isGlassContainer && "m-0",
        !isGlassContainer && "border-0 outline-none",
        "leading-none",
        "transition-all",
        "overflow-visible",
        variantClasses[variant],
        paddingClasses,
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      style={{ lineHeight: 0, ...borderRadiusStyle, ...dimensionStyle }}
    >
      <span
        className={clsx(
          "flex items-center justify-center",
          !height && !width && iconSizeClasses[size],
          (height || width) && "w-full h-full",
          "m-0 p-0",
          "text-inherit",
          iconClassName
        )}
        style={{ display: "flex", lineHeight: 0, color: "inherit" }}
      >
        {children}
      </span>
    </button>
  );
}
