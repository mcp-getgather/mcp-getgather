import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import EmptyState from "@/components/EmptyState";
import PageHeader from "@/components/PageHeader";
import {
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
} from "lucide-react";

export default function Activities() {
  // Temporary dummy data for development
  const dummyActivities = [
    {
      id: "activity-001",
      name: "Web Scraping Session",
      timestamp: "2024-01-15 14:30:22",
      status: "completed",
      duration: "2m 34s"
    },
    {
      id: "activity-002", 
      name: "Form Automation",
      timestamp: "2024-01-15 13:15:10",
      status: "completed",
      duration: "1m 12s"
    }
  ];

  const hasActivities = dummyActivities.length > 0;

  if (!hasActivities) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8">
        <PageHeader
          title="Activity"
          description="View your recent activity and logs"
          badge={{
            text: "Activity Monitor",
            icon: Activity,
          }}
        />

        <EmptyState
          icon={Clock}
          title="No Recent Activity"
          description="Your getgather operations and activity logs will appear here."
          action={
            <Button className="bg-indigo-600 hover:bg-indigo-700">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Activity
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <PageHeader
        title="Activity"
        description="View your recent activity and logs"
        badge={{
          text: "Activity Monitor",
          icon: Activity,
        }}
      />

      <div className="space-y-4">
        <Card className="border-0 shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <CardTitle className="text-base">
                    Data extraction completed
                  </CardTitle>
                  <CardDescription>Amazon order history</CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Badge variant="default" className="bg-green-100 text-green-800">
                  Success
                </Badge>
                <Link to="/replay?id=activity-001">
                  <Button variant="outline" size="sm">View Replay</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-gray-600">2 minutes ago</p>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <AlertCircle className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <CardTitle className="text-base">
                    Authentication required
                  </CardTitle>
                  <CardDescription>Netflix account access</CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <Badge
                  variant="secondary"
                  className="bg-orange-100 text-orange-800"
                >
                  Pending
                </Badge>
                <Link to="/replay?id=activity-002">
                  <Button variant="outline" size="sm">View Replay</Button>
                </Link>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-gray-600">5 minutes ago</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
