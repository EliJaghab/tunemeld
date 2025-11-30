import type { Meta, StoryObj } from "@storybook/react";
import { PlayIcon } from "./PlayIcon";

const meta = {
  title: "Components/Icons/PlayIcon",
  component: PlayIcon,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof PlayIcon>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex flex-col gap-8 p-8">
      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          Mobile Size (sm)
        </h3>
        <div className="flex items-center gap-4">
          <div className="bg-white/60 dark:bg-gray-700/60 p-2 rounded-full">
            <PlayIcon className="w-3.5 h-3.5 text-black dark:text-white" />
          </div>
          <span className="text-sm text-black dark:text-white">
            Mobile: w-3.5 h-3.5 (14px)
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          Desktop Size (sm)
        </h3>
        <div className="flex items-center gap-4">
          <div className="bg-white/60 dark:bg-gray-700/60 p-2 rounded-full">
            <PlayIcon
              className="desktop:w-4 desktop:h-4 text-black dark:text-white"
            />
          </div>
          <span className="text-sm text-black dark:text-white">
            Desktop: w-4 h-4 (16px)
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          Medium Size (md)
        </h3>
        <div className="flex items-center gap-4">
          <div className="bg-white/60 dark:bg-gray-700/60 p-2 rounded-full">
            <PlayIcon
              className="w-4 h-4 desktop:w-5 desktop:h-5 text-black
                dark:text-white"
            />
          </div>
          <span className="text-sm text-black dark:text-white">
            Mobile: 16px / Desktop: 20px
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          Large Size (lg)
        </h3>
        <div className="flex items-center gap-4">
          <div className="bg-white/60 dark:bg-gray-700/60 p-2 rounded-full">
            <PlayIcon
              className="w-5 h-5 desktop:w-6 desktop:h-6 text-black
                dark:text-white"
            />
          </div>
          <span className="text-sm text-black dark:text-white">
            Mobile: 20px / Desktop: 24px
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          In Glass Container (as used in MediaPlayer)
        </h3>
        <div className="flex items-center gap-4">
          <div
            className="bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border
              border-white/20 dark:border-gray-600/20 rounded-2xl p-2
              desktop:p-2.5
              shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]"
          >
            <PlayIcon className="w-full h-full text-black dark:text-white" />
          </div>
          <span className="text-sm text-black dark:text-white">
            Glass container with full width/height
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          Comparison: Play vs Pause
        </h3>
        <div className="flex items-center gap-4">
          <div className="bg-white/60 dark:bg-gray-700/60 p-2 rounded-full">
            <PlayIcon className="w-5 h-5 text-black dark:text-white" />
          </div>
          <div className="bg-white/60 dark:bg-gray-700/60 p-2 rounded-full">
            <img src="./images/pause.svg" alt="Pause" className="w-5 h-5" />
          </div>
          <span className="text-sm text-black dark:text-white">
            Side by side comparison
          </span>
        </div>
      </div>
    </div>
  ),
};

export const Interactive: Story = {
  render: () => {
    const [isPlaying, setIsPlaying] = React.useState(false);

    return (
      <div className="flex flex-col gap-8 p-8">
        <h3 className="text-lg font-semibold text-black dark:text-white">
          Interactive Play/Pause Toggle
        </h3>
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="bg-white/60 dark:bg-gray-700/60 backdrop-blur-md border
            border-white/20 dark:border-gray-600/20 rounded-2xl p-2
            desktop:p-2.5
            shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_4px_12px_rgba(0,0,0,0.1)]
            w-12 h-12 desktop:w-14 desktop:h-14 flex items-center justify-center
            hover:scale-110 transition-transform"
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <img
              src="./images/pause.svg"
              alt="Pause"
              className="w-full h-full object-contain"
            />
          ) : (
            <PlayIcon className="w-full h-full text-black dark:text-white" />
          )}
        </button>
        <span className="text-sm text-black dark:text-white">
          Click to toggle between play and pause
        </span>
      </div>
    );
  },
};
