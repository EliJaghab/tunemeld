import React, { useEffect } from "react";
import clsx from "clsx";
import GlassSurface from "@/v2/components/shared/GlassSurface";
import { CloseButton } from "@/v2/components/shared/CloseButton";

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

    if (playlistUrl) {
      window.open(playlistUrl, "_blank", "noopener,noreferrer");
    }
  };

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
          className="!items-start !justify-start"
        >
          <div
            className={clsx(
              "p-5 text-left",
              "!flex !flex-col !items-start !justify-start",
              playlistUrl && "cursor-pointer"
            )}
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
            <CloseButton
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              ariaLabel="Close modal"
              position="top-right"
            />
            <div className={clsx("relative")}>{children}</div>
          </div>
        </GlassSurface>
      </div>
    </>
  );
}
