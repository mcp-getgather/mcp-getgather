import { useSearchParams } from "react-router";
import { RRWebPlayer } from "@/components/rrweb-player";
import { useState, useEffect } from "react";

export function ReplayPage() {
  const [searchParams] = useSearchParams();
  const activityId = searchParams.get("id");
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoPlay, setAutoPlay] = useState(true);
  const [loop, setLoop] = useState(true);

  useEffect(() => {
    const loadEvents = async () => {
      if (!activityId) {
        setError("No activity ID provided");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/activities/recordings?activity_id=${activityId}`);
        if (!response.ok) {
          throw new Error("Failed to load events");
        }
        const data = await response.json();
        setEvents(data.events);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, [activityId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Activity Replay</h1>
          <p className="text-gray-600">Loading replay data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Activity Replay</h1>
          <p className="text-red-600">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Activity Replay</h1>
        <p className="text-gray-600">
          Replaying activity {activityId || "unknown"} ({events.length} events)
        </p>
      </div>
      
      {/* Playback Controls */}
      <div className="flex justify-center space-x-4 text-sm">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={autoPlay}
            onChange={(e) => setAutoPlay(e.target.checked)}
            className="rounded"
          />
          <span>Auto Play</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={loop}
            onChange={(e) => setLoop(e.target.checked)}
            className="rounded"
          />
          <span>Loop</span>
        </label>
      </div>
      
      <div className="w-full max-w-7xl mx-auto">
        <RRWebPlayer events={events} autoPlay={autoPlay} loop={loop} />
      </div>
    </div>
  );
}