import { useEffect, useRef } from "react";

interface RRWebPlayerProps {
  events: any[];
  width?: number;
  height?: number;
}

export function RRWebPlayer({ events }: RRWebPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || !events.length) return;

    let isDestroyed = false;

    // Dynamically import rrweb-player since it's not built for SSR
    const initializePlayer = async () => {
      try {
        // Prevent initialization if component was unmounted
        if (isDestroyed || !containerRef.current) return;

        // Clean up previous player instance properly
        if (playerRef.current && typeof playerRef.current.$destroy === 'function') {
          playerRef.current.$destroy();
          playerRef.current = null;
        }

        // Clear container completely
        containerRef.current.innerHTML = '';

        // Dynamically import rrweb-player
        const rrwebPlayer = (await import('rrweb-player')).default;

        // Prevent initialization if component was unmounted during import
        if (isDestroyed || !containerRef.current) return;

        // Get original dimensions from first event
        const originalWidth = events[0]?.data?.width || 1920;
        const originalHeight = events[0]?.data?.height || 1080;
        
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
            autoPlay: false, // Don't auto-play, let user control
            speed: 0.5, // Start at half speed for better viewing
            showController: true,
            speedOption: [0.25, 0.5, 1, 2, 4, 8], // Add slower speed options
          },
        });

      } catch (error) {
        console.error('Error initializing rrweb player:', error);
        // Show error placeholder only if component is still mounted
        if (!isDestroyed && containerRef.current) {
          containerRef.current.innerHTML = `
            <div style="width: 100%; min-height: 400px; background: #f5f5f5; display: flex; align-items: center; justify-content: center; border: 1px solid #ddd; border-radius: 8px;">
              <div style="text-align: center; color: #666;">
                <h3>RRWeb Player Error</h3>
                <p>Failed to initialize replay</p>
                <p>Events: ${events.length}</p>
              </div>
            </div>
          `;
        }
      }
    };

    initializePlayer();

    // Handle window resize
    const handleResize = () => {
      if (playerRef.current && containerRef.current) {
        // Recalculate dimensions on resize
        const originalWidth = events[0]?.data?.width || 1920;
        const originalHeight = events[0]?.data?.height || 1080;
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
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup function
    return () => {
      isDestroyed = true;
      window.removeEventListener('resize', handleResize);
      if (playerRef.current && typeof playerRef.current.$destroy === 'function') {
        playerRef.current.$destroy();
        playerRef.current = null;
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [events]);

  if (!events.length) {
    return (
      <div className="rrweb-player" style={{ width: '100%', minHeight: '400px' }}>
        <div style={{ 
          width: '100%', 
          height: '400px', 
          background: '#f5f5f5', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          border: '1px solid #ddd', 
          borderRadius: '8px' 
        }}>
          <div style={{ textAlign: 'center', color: '#666' }}>
            <h3>No Events</h3>
            <p>No recording events to replay</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="rrweb-player" 
      style={{ 
        width: '100%',
        minHeight: '400px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }} 
    />
  );
}