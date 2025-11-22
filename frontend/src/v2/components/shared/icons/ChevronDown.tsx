import React from "react";
import clsx from "clsx";

interface IconProps {
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
}

export function ChevronDown({ className, onClick }: IconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={clsx("cursor-pointer", className)}
      onClick={onClick}
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}
