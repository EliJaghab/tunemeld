import React, { useContext } from "react";
import { ThemeContext } from "@/v2/ThemeContext";
import { THEME } from "@/v2/constants";
import { Dither } from "@/v2/components/shared";

export function TuneMeldBackground(): React.ReactElement {
  const [theme] = useContext(ThemeContext);
  const invertPalette = theme === THEME.LIGHT;

  return (
    <Dither
      className="pointer-events-none absolute inset-0 z-0 h-full w-full select-none"
      waveColor={[0.2, 0.2, 0.2]}
      disableAnimation={false}
      enableMouseInteraction={true}
      mouseRadius={0.2}
      colorNum={3}
      waveAmplitude={0.25}
      waveFrequency={2}
      waveSpeed={0.05}
      invertPalette={invertPalette}
    />
  );
}
