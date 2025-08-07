import React, { useCallback } from "react";
import { Outlet, useLocation } from "react-router";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useNavigate } from "react-router";

function getActiveTab(pathname: string) {
  switch (pathname) {
    case "/":
      return "get-started";
    case "/live-view":
      return "live-view";
    case "/activities":
      return "activity";
    case "/settings":
      return "settings";
    default:
      return null;
  }
}

export function Root() {
  const [bannerVisible, setBannerVisible] = React.useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const onHandleTabChange = useCallback(
    (value: string) => {
      switch (value) {
        case "get-started":
          navigate("/");
          break;
        case "live-view":
          navigate("/live-view");
          break;
        case "activity":
          navigate("/activities");
          break;
        case "settings":
          navigate("/settings");
          break;
      }
    },
    [navigate],
  );

  // Don't show banner on unknown routes (404)
  const isKnownRoute = ["/", "/live-view", "/activities", "/settings"].includes(
    location.pathname,
  );
  const showBanner = bannerVisible && isKnownRoute;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Top Banner */}
      {showBanner && (
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-3 relative">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm font-medium">
                Come to GetGather Studio to help your agent when it gets stuck
                with access
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10 h-6 w-6"
              onClick={() => setBannerVisible(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                GG
              </div>
              <h1 className="text-xl font-semibold text-gray-900">
                GetGather Studio
              </h1>
            </div>
          </div>

          {/* Navigation Tabs - Only show on known routes */}
          {isKnownRoute && (
            <div className="mt-6">
              <Tabs
                value={getActiveTab(location.pathname) || "get-started"}
                onValueChange={onHandleTabChange}
                className="w-full"
              >
                <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-4">
                  <TabsTrigger value="get-started" className="text-sm">
                    Get Started
                  </TabsTrigger>
                  <TabsTrigger value="live-view" className="text-sm">
                    Live View
                  </TabsTrigger>
                  <TabsTrigger value="activity" className="text-sm">
                    Activity
                  </TabsTrigger>
                  <TabsTrigger value="settings" className="text-sm">
                    Settings
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
