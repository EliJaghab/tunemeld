import React, { useState, useRef, useEffect } from "react";
import { truncateTextForLines } from "@/v2/lib/truncateText";

interface PlaylistDescriptionProps {
  description: string | undefined;
  serviceName: string;
  playlistName?: string | undefined;
  serviceDisplayName?: string | undefined;
  onOpenModal: (content: {
    serviceDisplayName?: string;
    playlistName?: string;
    description?: string;
  }) => void;
  className?: string;
}

export function PlaylistDescription({
  description,
  serviceName,
  playlistName,
  serviceDisplayName,
  onOpenModal,
  className = "",
}: PlaylistDescriptionProps): React.ReactElement {
  const [isTruncated, setIsTruncated] = useState(false);
  const [displayText, setDisplayText] = useState("");
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (textRef.current && description) {
      const element = textRef.current;

      const testElement = document.createElement("div");
      testElement.style.position = "absolute";
      testElement.style.visibility = "hidden";
      testElement.style.width = getComputedStyle(element).width;
      testElement.style.font = getComputedStyle(element).font;
      testElement.style.fontSize = getComputedStyle(element).fontSize;
      testElement.style.fontFamily = getComputedStyle(element).fontFamily;
      testElement.style.fontWeight = getComputedStyle(element).fontWeight;
      testElement.style.lineHeight = getComputedStyle(element).lineHeight;
      testElement.textContent = description;

      element.parentElement?.appendChild(testElement);

      const lineHeight = parseFloat(getComputedStyle(testElement).lineHeight);
      const maxHeight = lineHeight * 4;
      const needsTruncation = testElement.scrollHeight > maxHeight;

      setIsTruncated(needsTruncation);

      if (needsTruncation) {
        const reserveSpace =
          typeof window !== "undefined" &&
          window.matchMedia("(min-width: 768px)").matches
            ? 30
            : 16;
        const truncated = truncateTextForLines(
          description,
          4,
          testElement,
          reserveSpace,
        );
        setDisplayText(truncated);
      } else {
        setDisplayText(description);
      }

      element.parentElement?.removeChild(testElement);
    }
  }, [description]);

  return (
    <>
      <div
        id={`${serviceName}-title-description`}
        className={`relative h-full overflow-hidden text-xs leading-[1.1rem] tracking-tight desktop:text-base desktop:leading-6 desktop:tracking-normal text-black dark:text-white ${className}`}
      >
        <div ref={textRef}>{displayText}</div>
        {isTruncated && (
          <button
            onClick={() =>
              onOpenModal({
                ...(serviceDisplayName && { serviceDisplayName }),
                ...(playlistName && { playlistName }),
                ...(description && { description }),
              })
            }
            className="font-semibold text-xs desktop:text-base text-black dark:text-white hover:underline absolute bottom-0 right-0"
          >
            ...more
          </button>
        )}
      </div>
    </>
  );
}
