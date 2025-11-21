import React, { useEffect } from "react";
import GlassSurface from "@/v2/components/shared/GlassSurface";

interface ServicePlaylistDescriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  maxWidth?: string;
}

export function ServicePlaylistDescriptionModal({
  isOpen,
  onClose,
  children,
  maxWidth = "600px",
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

  return (
    <>
      <div className="fixed inset-0 bg-black/15 z-[1000]" onClick={onClose} />
      <div
        className="fixed z-[1001]"
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
          <div className="p-5">
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
            <button
              onClick={onClose}
              className="absolute top-4 right-4 w-8 h-8 bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border border-white/20 dark:border-gray-600/20 rounded-full text-lg text-black dark:text-white cursor-pointer z-10 flex items-center justify-center font-mono leading-none shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)] transition-all hover:bg-white/80 dark:hover:bg-gray-600/80 hover:border-white/30 dark:hover:border-gray-500/30 hover:scale-105 hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_6px_16px_rgba(0,0,0,0.15)]"
              aria-label="Close modal"
            >
              ×
            </button>
            <div className="relative">{children}</div>
          </div>
        </GlassSurface>
      </div>
    </>
  );
}
