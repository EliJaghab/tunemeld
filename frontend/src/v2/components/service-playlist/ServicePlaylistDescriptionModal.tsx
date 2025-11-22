import React, { useEffect } from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";

interface ServicePlaylistDescriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  maxWidth?: string;
  playlistUrl?: string;
  playlistName?: string;
  serviceDisplayName?: string;
}

export function ServicePlaylistDescriptionModal({
  isOpen,
  onClose,
  children,
  maxWidth = "600px",
  playlistUrl,
  playlistName,
  serviceDisplayName,
}: ServicePlaylistDescriptionModalProps): React.ReactElement | null {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleModalClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking the close button, link emoji, or their children
    const target = e.target as HTMLElement;
    if (
      target.closest('button[aria-label="Close modal"]') ||
      target.closest('button[aria-label="Close modal"]')?.contains(target) ||
      target.closest("a[href]") ||
      target.tagName === "A"
    ) {
      return;
    }

    // Navigate to playlist URL if available
    if (playlistUrl) {
      window.open(playlistUrl, "_blank", "noopener,noreferrer");
    }
  };

  // Create proper label for accessibility and hover tooltip
  const getModalLabel = () => {
    if (playlistName && serviceDisplayName) {
      return `Visit ${playlistName} on ${serviceDisplayName}`;
    } else if (playlistName) {
      return `Visit ${playlistName} playlist`;
    } else if (serviceDisplayName) {
      return `Visit ${serviceDisplayName} playlist`;
    }
    return "Visit playlist";
  };

  return (
    <>
      <div
        className={clsx("fixed inset-0 bg-black/15 z-[1000]")}
        onClick={onClose}
      />
      <div
        className={clsx("fixed z-[1001]")}
        style={{
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
          width: "90%",
          maxWidth,
        }}
      >
        <GlassSurface
          width="100%"
          height="auto"
          borderRadius={32}
          backgroundOpacity={0.5}
          borderWidth={0.5}
          blur={20}
        >
          <div
            className={clsx("p-5", playlistUrl && "cursor-pointer")}
            onClick={handleModalClick}
            title={playlistUrl ? getModalLabel() : undefined}
            aria-label={playlistUrl ? getModalLabel() : undefined}
            role={playlistUrl ? "button" : undefined}
            tabIndex={playlistUrl ? 0 : undefined}
            onKeyDown={(e) => {
              if (playlistUrl && (e.key === "Enter" || e.key === " ")) {
                e.preventDefault();
                window.open(playlistUrl, "_blank", "noopener,noreferrer");
              }
            }}
          >
            <div
              className={clsx(
                "absolute top-0 left-0 right-0 h-px",
                "bg-gradient-to-r from-transparent via-white/40 to-transparent"
              )}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              className={clsx(
                "absolute top-4 right-4 w-8 h-8",
                "bg-white/60 dark:bg-gray-700/60 backdrop-blur-md",
                "border border-white/20 dark:border-gray-600/20",
                "rounded-full text-lg",
                "text-black dark:text-white",
                "cursor-pointer z-10",
                "flex items-center justify-center",
                "font-mono leading-none",
                "shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]",
                "transition-all",
                "hover:bg-white/80 dark:hover:bg-gray-600/80",
                "hover:border-white/30 dark:hover:border-gray-500/30",
                "hover:scale-105",
                "hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_6px_16px_rgba(0,0,0,0.15)]"
              )}
              aria-label="Close modal"
            >
              ×
            </button>
            <div className={clsx("relative")}>{children}</div>
          </div>
        </GlassSurface>
      </div>
    </>
  );
}
