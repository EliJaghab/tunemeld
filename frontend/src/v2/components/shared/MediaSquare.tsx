import React, { useEffect, useRef } from "react";
import clsx from "clsx";

interface HlsStatic {
  isSupported(): boolean;
  Events: {
    MANIFEST_PARSED: string;
  };
  new (): {
    loadSource(url: string): void;
    attachMedia(video: HTMLVideoElement): void;
    on(event: string, callback: () => void): void;
    destroy(): void;
  };
}

declare global {
  interface Window {
    Hls: HlsStatic;
  }
}

interface MediaSquareProps {
  src: string;
  type: "image" | "video";
  alt?: string | undefined;
}

export function MediaSquare({
  src,
  type,
  alt = "",
}: MediaSquareProps): React.ReactElement {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (type !== "video" || !videoRef.current) return undefined;

    const video = videoRef.current;
    const Hls = window.Hls;

    if (Hls && Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(src);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });
      return () => hls.destroy();
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      video.play().catch(() => {});
    }
    return undefined;
  }, [type, src]);

  return type === "video" ? (
    <div
      className={clsx(
        "video-container rounded-media overflow-hidden aspect-square w-full",
        "bg-black/10 dark:bg-white/10"
      )}
      style={{
        minHeight: 0,
        minWidth: 0,
        position: "relative",
      }}
    >
      <video
        ref={videoRef}
        className={clsx("w-full h-full object-cover rounded-media")}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
        }}
        muted
        autoPlay
        loop
        playsInline
        controlsList="nodownload nofullscreen noremoteplayback"
      />
    </div>
  ) : (
    <div
      className={clsx(
        "image-placeholder rounded-media aspect-square w-full",
        "bg-cover bg-center"
      )}
      style={{
        backgroundImage: `url("${src}")`,
      }}
      role="img"
      aria-label={alt}
    />
  );
}
