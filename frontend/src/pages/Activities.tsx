import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, RefreshCw, ExternalLink } from "lucide-react";

export default function Activities() {
  // Temporary dummy data for development
  const dummyActivities = [
    {
      id: "activity-1",
      name: "Web Scraping Session",
      timestamp: "2024-01-15 14:30:22",
      status: "completed",
      duration: "2m 34s"
    },
    {
      id: "activity-2", 
      name: "Form Automation",
      timestamp: "2024-01-15 13:15:10",
      status: "completed",
      duration: "1m 12s"
    }
  ];

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
          <Button size="sm" variant="outline">
            <RefreshCw className="h-4 w-4" />
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
              <ul className="divide-y divide-gray-100">
                {[
                  {
                    title: "bbc_get_bookmarks",
                    tag: "BBC",
                    time: "(2s)",
                    active: true,
                  },
                  {
                    title: "goodreads_get_book_list",
                    tag: "Goodreads",
                    time: "1h ago (20s)",
                  },
                  {
                    title: "goodreads_auth",
                    tag: "Goodreads",
                    time: "1h ago (20s)",
                  },
                  {
                    title: "amazon_get_orders",
                    tag: "Amazon",
                    time: "1h ago (20s)",
                  },
                  {
                    title: "amazon_auth",
                    tag: "Amazon",
                    time: "1h ago (20s)",
                  },
                  {
                    title: "tokopedia_search_product",
                    tag: "Tokopedia",
                    time: "1h ago (20s)",
                  },
                  {
                    title: "ebird_get_explore_species_list",
                    tag: "eBird",
                    time: "1h ago (20s)",
                  },
                ].map((item, idx) => (
                  <li key={idx} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span
                          className={`h-2.5 w-2.5 rounded-full ${
                            item.active ? "bg-green-500" : "bg-gray-300"
                          }`}
                        />
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-900">
                            {item.title}
                          </span>
                          {item.tag ? (
                            <Badge
                              variant="secondary"
                              className="bg-indigo-50 text-indigo-700"
                            >
                              {item.tag}
                            </Badge>
                          ) : null}
                          {idx === 0 ? (
                            <ExternalLink className="h-3.5 w-3.5 text-gray-400" />
                          ) : null}
                        </div>
                      </div>
                      <span className="text-xs text-gray-500">{item.time}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Right column: Summary */}
        <div className="space-y-6">
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Current Task</CardTitle>
              <CardDescription>
                Retrieving recent Amazon orders and checking return expiration
                dates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-2 w-full rounded-full bg-gray-100">
                <div
                  className="h-2 rounded-full bg-indigo-600"
                  style={{ width: "65%" }}
                />
              </div>
              <div className="mt-2 text-right text-xs text-gray-500">65%</div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Activity Types</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span>Page Navigation</span>
                  <span className="text-gray-600">45</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Form Submission</span>
                  <span className="text-gray-600">23</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Data Extraction</span>
                  <span className="text-gray-600">31</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Click Action</span>
                  <span className="text-gray-600">28</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}