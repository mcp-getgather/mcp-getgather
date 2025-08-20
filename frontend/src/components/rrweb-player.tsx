import { useEffect, useRef, useState } from "react";
import "rrweb-player/dist/style.css";

// RRWeb event type definition
interface RRWebEvent {
  type: number;
  data: Record<string, unknown>;
  timestamp: number;
  [key: string]: unknown;
}

// RRWeb player interface
interface RRWebPlayerInstance {
  $destroy(): void;
  $set(props: { width: number; height: number }): void;
  triggerResize(): void;
  goto(time: number, autoPlay?: boolean): void;
  addEventListener(event: string, handler: () => void): void;
  [key: string]: unknown; // Allow additional properties
}

interface RRWebPlayerProps {
  events: RRWebEvent[];
  width?: number;
  height?: number;
}

export function RRWebPlayer({ events }: RRWebPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<RRWebPlayerInstance | null>(null);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !events.length) return;

    let isDestroyed = false;
    setHasError(false);

    // Dynamically import rrweb-player since it's not built for SSR
    const initializePlayer = async () => {
      try {
        // Prevent initialization if component was unmounted
        if (isDestroyed || !containerRef.current) return;

        // Clean up previous player instance properly
        if (
          playerRef.current &&
          typeof playerRef.current.$destroy === "function"
        ) {
          playerRef.current.$destroy();
          playerRef.current = null;
        }

        // Clear container completely
        containerRef.current.innerHTML = "";

        // Dynamically import rrweb-player
        const rrwebPlayer = (await import("rrweb-player")).default;

        // Prevent initialization if component was unmounted or no events to replay
        if (isDestroyed || !containerRef.current || !events || !events.length)
          return;

        // Get original dimensions from first event
        const originalWidth = Number(events[0]?.data?.width) || 1920;
        const originalHeight = Number(events[0]?.data?.height) || 1080;

        // Calculate responsive dimensions
        const containerWidth = containerRef.current.clientWidth;
        const maxWidth = containerWidth - 40; // Account for padding
        const maxHeight = window.innerHeight * 0.7; // Use 70% of viewport

        // Calculate scale to maintain aspect ratio
        const scaleX = maxWidth / originalWidth;
        const scaleY = maxHeight / originalHeight;
        const scale = Math.min(scaleX, scaleY, 1); // Don't scale up

        const playerWidth = originalWidth * scale;
        const playerHeight = originalHeight * scale;

        // Initialize rrweb-player with responsive dimensions
        playerRef.current = new rrwebPlayer({
          target: containerRef.current,
          props: {
            events,
            width: playerWidth,
            height: playerHeight,
            maxScale: 0, // Allow unlimited scaling for responsiveness
            autoPlay: true,
            speed: 1,
            showController: true,
            speedOption: [1, 0.25, 0.5, 2, 4, 8], // Default to 1x speed first
            skipInactive: true, // Skip blank/inactive periods automatically
          },
        }) as unknown as RRWebPlayerInstance;

        // Add loop functionality (always enabled)
        if (playerRef.current) {
          playerRef.current.addEventListener("finish", () => {
            console.log("Replay finished, restarting loop...");
            // Restart the replay from beginning
            playerRef.current?.goto(0, true); // Go to start and auto-play
          });
        }
      } catch (error) {
        console.error("Error initializing rrweb player:", error);
        if (!isDestroyed) {
          setHasError(true);
        }
      }
    };

    initializePlayer();

    // Handle window resize
    const handleResize = () => {
      if (
        !playerRef.current ||
        !containerRef.current ||
        !events ||
        !events.length
      )
        return;

      // Recalculate dimensions on resize
      const originalWidth = Number(events[0]?.data?.width) || 1920;
      const originalHeight = Number(events[0]?.data?.height) || 1080;
      const containerWidth = containerRef.current.clientWidth;
      const maxWidth = containerWidth - 40;
      const maxHeight = window.innerHeight * 0.7;

      const scaleX = maxWidth / originalWidth;
      const scaleY = maxHeight / originalHeight;
      const scale = Math.min(scaleX, scaleY, 1);

      const newWidth = originalWidth * scale;
      const newHeight = originalHeight * scale;

      // Update player dimensions
      playerRef.current.$set({
        width: newWidth,
        height: newHeight,
      });
      playerRef.current.triggerResize();
    };

    window.addEventListener("resize", handleResize);

    // Cleanup function
    return () => {
      isDestroyed = true;
      window.removeEventListener("resize", handleResize);

      // Copy refs to variables to avoid React hooks warning about stale refs
      const player = playerRef.current;
      const container = containerRef.current;

      if (player && typeof player.$destroy === "function") {
        player.$destroy();
        playerRef.current = null;
      }

      if (container) {
        container.innerHTML = "";
      }
    };
  }, [events]);

  if (!events.length) {
    return (
      <div className="rrweb-player w-full min-h-[400px]">
        <div className="w-full h-[400px] bg-gray-100 flex items-center justify-center border border-gray-300 rounded-lg">
          <div className="text-center text-gray-600">
            <h3>No Events</h3>
            <p>No recording events to replay</p>
          </div>
        </div>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="rrweb-player w-full min-h-[400px]">
        <div className="w-full h-[400px] bg-gray-100 flex items-center justify-center border border-gray-300 rounded-lg">
          <div className="text-center text-gray-600">
            <h3>Unable to Load Replay</h3>
            <p>Failed to initialize the replay player</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="rrweb-player w-full min-h-[400px] flex justify-center items-center"
    />
  );
}
