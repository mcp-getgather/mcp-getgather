import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, RefreshCw, ExternalLink, Play } from "lucide-react";
import { useState, useEffect } from "react";
import { Link } from "react-router";
import { ApiService, type Activity } from "@/lib/api";

export default function Activities() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  const loadActivities = async () => {
    try {
      setLoading(true);
      const activitiesData = await ApiService.getActivities();
      setActivities(activitiesData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, []);

  const filteredActivities = activities.filter(activity =>
    activity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    activity.brand_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDuration = (executionTimeMs: number | null): string => {
    if (!executionTimeMs) return "N/A";
    const seconds = Math.floor(executionTimeMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffHours > 24) {
      return date.toLocaleDateString();
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes}m ago`;
    } else {
      return 'Just now';
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Activity</h1>
          <p className="text-muted-foreground mt-1">
            Track all agent activities and monitor performance in detail
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button size="sm" variant="outline" onClick={loadActivities} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1 flex items-center gap-3 bg-white border-1 p-4 rounded-lg">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search activities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-md border border-gray-200 bg-white pl-9 pr-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Activity feed */}
        <div className="lg:col-span-2">
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Recent Activities</CardTitle>
                  <CardDescription>Activity Feed</CardDescription>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <div className="flex items-center gap-2 text-green-600">
                    <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                    Live Updates
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                  <span className="ml-2 text-gray-500">Loading activities...</span>
                </div>
              ) : error ? (
                <div className="text-center py-8">
                  <p className="text-red-600">{error}</p>
                  <Button onClick={loadActivities} variant="outline" className="mt-2">
                    Retry
                  </Button>
                </div>
              ) : filteredActivities.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">
                    {searchTerm ? 'No activities match your search' : 'No activities found'}
                  </p>
                </div>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {filteredActivities.map((activity) => (
                    <li key={activity.id} className="py-3 first:pt-0 last:pb-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span
                            className={`h-2.5 w-2.5 rounded-full ${
                              activity.end_time ? "bg-gray-300" : "bg-green-500"
                            }`}
                          />
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-900">
                              {activity.name}
                            </span>
                            {activity.brand_id && (
                              <Badge
                                variant="secondary"
                                className="bg-indigo-50 text-indigo-700 capitalize"
                              >
                                {activity.brand_id}
                              </Badge>
                            )}
                            {!activity.end_time && (
                              <ExternalLink className="h-3.5 w-3.5 text-gray-400" />
                            )}
                            {activity.end_time && activity.recording_count > 0 && (
                              <Link 
                                to={`/replay?id=${activity.id}`}
                                className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
                              >
                                <Play className="h-3 w-3" />
                                Replay ({activity.recording_count} events)
                              </Link>
                            )}
                          </div>
                        </div>
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(activity.start_time)} ({formatDuration(activity.execution_time_ms)})
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column: Summary */}
        <div className="space-y-6">
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Statistics</CardTitle>
              <CardDescription>
                Activity overview and performance metrics
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span>Total Activities</span>
                  <span className="text-gray-900 font-medium">{activities.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Completed</span>
                  <span className="text-green-600 font-medium">
                    {activities.filter(a => a.end_time).length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>In Progress</span>
                  <span className="text-yellow-600 font-medium">
                    {activities.filter(a => !a.end_time).length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Average Duration</span>
                  <span className="text-gray-600">
                    {(() => {
                      const completedActivities = activities.filter(a => a.execution_time_ms);
                      if (completedActivities.length === 0) return 'N/A';
                      const avgMs = completedActivities.reduce((sum, a) => sum + a.execution_time_ms!, 0) / completedActivities.length;
                      return formatDuration(avgMs);
                    })()}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Brands</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                {(() => {
                  const brandCounts = activities.reduce((acc, activity) => {
                    const brand = activity.brand_id || 'Unknown';
                    acc[brand] = (acc[brand] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>);
                  
                  return Object.entries(brandCounts)
                    .sort(([,a], [,b]) => b - a)
                    .slice(0, 5)
                    .map(([brand, count]) => (
                      <div key={brand} className="flex items-center justify-between">
                        <span className="capitalize">{brand}</span>
                        <span className="text-gray-600">{count}</span>
                      </div>
                    ));
                })()}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
