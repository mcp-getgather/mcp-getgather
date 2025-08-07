import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Eye, Activity, Clock } from "lucide-react";

type Operation = {
  id: number;
  operation: string;
  status: "success" | "pending";
  time: string;
};

export function LiveViewPage() {
  const operations: Operation[] = [
    {
      id: 1,
      operation: "Amazon search",
      status: "success",
      time: "2 seconds ago",
    },
    {
      id: 2,
      operation: "Netflix login",
      status: "pending",
      time: "5 seconds ago",
    },
    {
      id: 3,
      operation: "Google navigation",
      status: "success",
      time: "12 seconds ago",
    },
  ];

  function renderOperation(op: Operation) {
    return (
      <div
        key={op.id}
        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
      >
        <div>
          <p className="font-medium">{op.operation}</p>
          <p className="text-sm text-gray-500">{op.time}</p>
        </div>
        <Badge variant={op.status === "success" ? "default" : "secondary"}>
          {op.status}
        </Badge>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Live View</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Monitor GetGather operations in real-time and intervene when
          necessary.
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Sessions
            </CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
            <p className="text-xs text-muted-foreground">+2 from last hour</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Operations/min
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">24</div>
            <p className="text-xs text-muted-foreground">+12% from last hour</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Avg Response Time
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1.2s</div>
            <p className="text-xs text-muted-foreground">
              -0.3s from last hour
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Live Operations */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Operations</CardTitle>
          <CardDescription>
            Live stream of GetGather operations and their status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">{operations.map(renderOperation)}</div>
        </CardContent>
      </Card>
    </div>
  );
}
