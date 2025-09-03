import { RRWebPlayer, type RRWebEvent } from "@/components/rrweb-player";
import { $api } from "@/lib/api";
import { useSearchParams } from "react-router";

export function ReplayPage() {
  const [searchParams] = useSearchParams();
  const activityId = searchParams.get("id");
  if (!activityId) {
    return;
  }

  return <ReplayPageContent activityId={activityId} />;
}

function ReplayPageContent({ activityId }: { activityId: string }) {
  const { data, isLoading, error } = $api.useQuery(
    "get",
    "/activities/{activity_id}/recordings",
    {
      params: {
        path: { activity_id: activityId },
      },
    },
  );

  if (!data) {
    return null;
  }

  if (isLoading) {
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
          <p className="text-red-600">Error: {String(error)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900">Activity Replay</h1>
        <p className="text-gray-600">
          Replaying activity {activityId || "unknown"} ({data.events.length}{" "}
          events)
        </p>
      </div>

      <div className="w-full max-w-7xl mx-auto">
        <RRWebPlayer events={data.events as RRWebEvent[]} />
      </div>
    </div>
  );
}
