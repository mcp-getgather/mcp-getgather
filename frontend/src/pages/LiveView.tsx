import { Button } from "@/components/ui/button";
import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import { Activity, Play } from "lucide-react";

export default function LiveView() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <PageHeader
        title="Live View"
        description="Monitor your getgather operations in real-time"
        badge={{
          text: "Real-time Monitoring",
          icon: Activity,
        }}
      />

      <EmptyState
        icon={Play}
        title="No Active Operations"
        description="Start a getgather operation to see real-time monitoring here."
        action={
          <Button className="bg-indigo-600 hover:bg-indigo-700">
            <Play className="w-4 h-4 mr-2" />
            Start Monitoring
          </Button>
        }
      />
    </div>
  );
}
