import React, { useEffect, useRef, useId } from "react";
import clsx from "clsx";

interface GlassSurfaceProps {
  children: React.ReactNode;
  width?: number | string;
  height?: number | string;
  borderRadius?: number;
  borderWidth?: number;
  brightness?: number;
  opacity?: number;
  blur?: number;
  displace?: number;
  backgroundOpacity?: number;
  saturation?: number;
  distortionScale?: number;
  redOffset?: number;
  greenOffset?: number;
  blueOffset?: number;
  xChannel?: string;
  yChannel?: string;
  mixBlendMode?: string;
  className?: string;
  style?: React.CSSProperties;
  onClick?: (e: React.MouseEvent) => void;
}

const GlassSurface: React.FC<GlassSurfaceProps> = ({
  children,
  width = 200,
  height = 80,
  borderRadius = 20,
  borderWidth = 0.07,
  brightness = 50,
  opacity = 0.93,
  blur = 11,
  displace = 0,
  backgroundOpacity = 0,
  saturation = 1.8,
  distortionScale = -25,
  redOffset = 0,
  greenOffset = 5,
  blueOffset = 10,
  xChannel = "R",
  yChannel = "G",
  mixBlendMode = "difference",
  className = "",
  style = {},
  onClick,
}) => {
  const uniqueId = useId().replace(/:/g, "-");
  const filterId = `glass-filter-${uniqueId}`;
  const redGradId = `red-grad-${uniqueId}`;
  const blueGradId = `blue-grad-${uniqueId}`;

  const containerRef = useRef<HTMLDivElement>(null);
  const feImageRef = useRef<SVGFEImageElement>(null);
  const redChannelRef = useRef<SVGFEDisplacementMapElement>(null);
  const greenChannelRef = useRef<SVGFEDisplacementMapElement>(null);
  const blueChannelRef = useRef<SVGFEDisplacementMapElement>(null);
  const gaussianBlurRef = useRef<SVGFEGaussianBlurElement>(null);

  const generateDisplacementMap = () => {
    const rect = containerRef.current?.getBoundingClientRect();
    const actualWidth = rect?.width || 400;
    const actualHeight = rect?.height || 200;
    const edgeSize = Math.min(actualWidth, actualHeight) * (borderWidth * 0.5);

    const svgContent = `
      <svg viewBox="0 0 ${actualWidth} ${actualHeight}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="${redGradId}" x1="100%" y1="0%" x2="0%" y2="0%">
            <stop offset="0%" stop-color="#0000"/>
            <stop offset="100%" stop-color="red"/>
          </linearGradient>
          <linearGradient id="${blueGradId}" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0000"/>
            <stop offset="100%" stop-color="blue"/>
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" fill="black"></rect>
        <rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" rx="${borderRadius}" fill="url(#${redGradId})" />
        <rect x="0" y="0" width="${actualWidth}" height="${actualHeight}" rx="${borderRadius}" fill="url(#${blueGradId})" style="mix-blend-mode: ${mixBlendMode}" />
        <rect x="${edgeSize}" y="${edgeSize}" width="${
          actualWidth - edgeSize * 2
        }" height="${
          actualHeight - edgeSize * 2
        }" rx="${borderRadius}" fill="hsl(0 0% ${brightness}% / ${opacity})" style="filter:blur(${blur}px)" />
      </svg>
    `;

    return `data:image/svg+xml,${encodeURIComponent(svgContent)}`;
  };

  const updateDisplacementMap = () => {
    feImageRef.current?.setAttribute("href", generateDisplacementMap());
  };

  useEffect(() => {
    updateDisplacementMap();
    [
      {
        ref: redChannelRef,
        offset: redOffset,
      },
      {
        ref: greenChannelRef,
        offset: greenOffset,
      },
      {
        ref: blueChannelRef,
        offset: blueOffset,
      },
    ].forEach(({ ref, offset }) => {
      if (ref.current) {
        ref.current.setAttribute(
          "scale",
          (distortionScale + offset).toString()
        );
        ref.current.setAttribute("xChannelSelector", xChannel);
        ref.current.setAttribute("yChannelSelector", yChannel);
      }
    });

    gaussianBlurRef.current?.setAttribute("stdDeviation", displace.toString());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    width,
    height,
    borderRadius,
    borderWidth,
    brightness,
    opacity,
    blur,
    displace,
    distortionScale,
    redOffset,
    greenOffset,
    blueOffset,
    xChannel,
    yChannel,
    mixBlendMode,
  ]);

  useEffect(() => {
    if (!containerRef.current) return;

    const resizeObserver = new ResizeObserver(() => {
      setTimeout(updateDisplacementMap, 0);
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setTimeout(updateDisplacementMap, 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [width, height]);

  const supportsSVGFilters = () => {
    const isWebkit =
      /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
    const isFirefox = /Firefox/.test(navigator.userAgent);

    if (isWebkit || isFirefox) {
      return false;
    }

    const div = document.createElement("div");
    div.style.backdropFilter = `url(#${filterId})`;
    return div.style.backdropFilter !== "";
  };

  const containerStyle = {
    ...style,
    width: typeof width === "number" ? `${width}px` : width,
    height: typeof height === "number" ? `${height}px` : height,
    borderRadius: `${borderRadius}px`,
    "--glass-frost": backgroundOpacity,
    "--glass-saturation": saturation,
    "--filter-id": `url(#${filterId})`,
  };

  const isSVG = supportsSVGFilters();
  const isDark =
    typeof document !== "undefined" &&
    document.documentElement.classList.contains("dark");

  // Check if background is explicitly set in style prop (for active buttons)
  const hasCustomBackground = style?.background !== undefined;

  // Base classes for all variants
  const baseClasses = [
    "relative flex items-center justify-center overflow-hidden",
    "transition-opacity duration-[260ms] ease-out",
  ];

  // SVG variant styles (complex backdrop-filter and box-shadow)
  const svgStyles =
    isSVG && !hasCustomBackground
      ? {
          background: `hsl(0 0% ${
            backgroundOpacity > 0 ? (isDark ? "0%" : "100%") : "0%"
          } / ${backgroundOpacity})`,
          backdropFilter: `var(--filter-id, url(#${filterId})) saturate(${saturation})`,
          boxShadow: `
      0 0 2px 1px color-mix(in oklch, ${
        isDark ? "white" : "black"
      }, transparent ${isDark ? "65%" : "92%"}) inset,
      0 0 10px 4px color-mix(in oklch, ${
        isDark ? "white" : "black"
      }, transparent ${isDark ? "85%" : "95%"}) inset,
      0px 4px 16px rgba(17, 17, 26, 0.05),
      0px 8px 24px rgba(17, 17, 26, 0.05),
      0px 16px 56px rgba(17, 17, 26, 0.05),
      0px 4px 16px rgba(17, 17, 26, ${isDark ? "0.05" : "0.02"}) inset,
      0px 8px 24px rgba(17, 17, 26, ${isDark ? "0.05" : "0.02"}) inset,
      0px 16px 56px rgba(17, 17, 26, ${isDark ? "0.05" : "0.02"}) inset
    `,
        }
      : {};

  const finalStyle = {
    ...containerStyle,
    ...svgStyles,
  };

  return (
    <div
      ref={containerRef}
      className={clsx(baseClasses, className)}
      style={finalStyle}
      onClick={onClick}
    >
      <svg
        className={clsx(
          "w-full h-full pointer-events-none absolute inset-0 opacity-0 -z-10"
        )}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <filter
            id={filterId}
            colorInterpolationFilters="sRGB"
            x="0%"
            y="0%"
            width="100%"
            height="100%"
          >
            <feImage
              ref={feImageRef}
              x="0"
              y="0"
              width="100%"
              height="100%"
              preserveAspectRatio="none"
              result="map"
            />

            <feDisplacementMap
              ref={redChannelRef}
              in="SourceGraphic"
              in2="map"
              id="redchannel"
              result="dispRed"
            />
            <feColorMatrix
              in="dispRed"
              type="matrix"
              values="1 0 0 0 0
                      0 0 0 0 0
                      0 0 0 0 0
                      0 0 0 1 0"
              result="red"
            />

            <feDisplacementMap
              ref={greenChannelRef}
              in="SourceGraphic"
              in2="map"
              id="greenchannel"
              result="dispGreen"
            />
            <feColorMatrix
              in="dispGreen"
              type="matrix"
              values="0 0 0 0 0
                      0 1 0 0 0
                      0 0 0 0 0
                      0 0 0 1 0"
              result="green"
            />

            <feDisplacementMap
              ref={blueChannelRef}
              in="SourceGraphic"
              in2="map"
              id="bluechannel"
              result="dispBlue"
            />
            <feColorMatrix
              in="dispBlue"
              type="matrix"
              values="0 0 0 0 0
                      0 0 0 0 0
                      0 0 1 0 0
                      0 0 0 1 0"
              result="blue"
            />

            <feBlend in="red" in2="green" mode="screen" result="rg" />
            <feBlend in="rg" in2="blue" mode="screen" result="output" />
            <feGaussianBlur
              ref={gaussianBlurRef}
              in="output"
              stdDeviation={displace > 0 ? displace.toString() : "0.3"}
            />
          </filter>
        </defs>
      </svg>

      <div
        className={clsx(
          "w-full h-full flex items-center justify-center p-0",
          "rounded-[inherit] relative z-10"
        )}
      >
        {children}
      </div>
    </div>
  );
};

export default GlassSurface;
