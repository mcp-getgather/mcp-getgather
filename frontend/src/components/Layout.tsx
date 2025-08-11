import { X } from "lucide-react";
import { useState } from "react";
import { Outlet, NavLink } from "react-router";

export default function Layout() {
  const [showBanner, setShowBanner] = useState(true);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Top Banner */}
      {showBanner && (
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            <span className="text-sm">
              Come to GetGather Portal to help your agent when it gets stuck
              with access
            </span>
          </div>
          <button
            onClick={() => setShowBanner(false)}
            className="text-white hover:text-gray-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <header className="px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
            GG
          </div>
          <h1 className="text-2xl font-bold text-slate-800">
            GetGather Portal
          </h1>
        </div>
      </header>

      {/* Navigation */}
      <div className="px-6">
        <nav className="w-full">
          <div className="flex gap-4 border-b border-gray-200 mb-8">
            <NavLink
              to="/welcome"
              className={({ isActive }) =>
                `px-4 py-2 border-b-2 transition-colors ${
                  isActive
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`
              }
            >
              Get Started
            </NavLink>
            <NavLink
              to="/live-view"
              className={({ isActive }) =>
                `px-4 py-2 border-b-2 transition-colors ${
                  isActive
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`
              }
            >
              Live View
            </NavLink>
            <NavLink
              to="/activities"
              className={({ isActive }) =>
                `px-4 py-2 border-b-2 transition-colors ${
                  isActive
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`
              }
            >
              Activity
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `px-4 py-2 border-b-2 transition-colors ${
                  isActive
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                }`
              }
            >
              Settings
            </NavLink>
          </div>
        </nav>

        {/* Main content area */}
        <Outlet />
      </div>
    </div>
  );
}
