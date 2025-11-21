import React from "react";
import clsx from "clsx";

interface CollapsibleSectionProps {
  isCollapsed: boolean;
  onToggle: () => void;
  header: React.ReactNode;
  children: React.ReactNode;
}

export function CollapsibleSection({
  isCollapsed,
  onToggle,
  header,
  children,
}: CollapsibleSectionProps) {
  return (
    <div className={clsx("w-full")}>
      <div
        onClick={onToggle}
        className={clsx("cursor-pointer select-none")}
        role="button"
        aria-expanded={!isCollapsed}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        {header}
      </div>

      {!isCollapsed && (
        <div className={clsx("mt-3 desktop:mt-4 overflow-hidden")}>
          {children}
        </div>
      )}
    </div>
  );
}
