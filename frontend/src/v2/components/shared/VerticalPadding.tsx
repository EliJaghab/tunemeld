import React from "react";

const VERTICAL_PADDING_SIZES = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

type VerticalPaddingSize = keyof typeof VERTICAL_PADDING_SIZES;

interface VerticalPaddingProps {
  size?: VerticalPaddingSize;
}

export function VerticalPadding({
  size = "md",
}: VerticalPaddingProps): React.ReactElement {
  const height = VERTICAL_PADDING_SIZES[size];

  return (
    <div
      aria-hidden="true"
      className="w-full"
      style={{ height: `${height}px` }}
    />
  );
}

export const VERTICAL_PADDING = VERTICAL_PADDING_SIZES;
