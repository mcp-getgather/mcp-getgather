import { X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router";

import { liveViewEnabled } from "@/lib/config";

export default function Layout() {
  const [showBanner, setShowBanner] = useState(true);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Top Banner */}
      {showBanner && (
        <div className="flex items-center justify-between bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 text-white">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-400"></div>
            <span className="text-sm">
              Come to GetGather Station to help your agent when it gets stuck with access
            </span>
          </div>
          <button
            onClick={() => setShowBanner(false)}
            className="text-white transition-colors hover:text-gray-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <header className="px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 text-lg font-bold text-white">
            GG
          </div>
          <h1 className="text-2xl font-bold text-slate-800">GetGather Station</h1>
        </div>
      </header>

      {/* Navigation */}
      <div className="px-6">
        <nav className="w-full">
          <div className="mb-8 flex gap-4 border-b border-gray-200">
            <NavItem href="/" label="Get Started" />
            {liveViewEnabled() && <NavItem href="/live-view" label="Live View" />}
            <NavItem href="/docs-mcp" label="MCP Docs" />
          </div>
        </nav>

        {/* Main content area */}
        <Outlet />
      </div>
    </div>
  );
}

function NavItem({ href, label }: { href: string; label: string }) {
  return (
    <NavLink
      to={href}
      className={({ isActive }) =>
        `border-b-2 px-4 py-2 transition-colors ${
          isActive
            ? "border-indigo-600 text-indigo-600"
            : "border-transparent text-gray-600 hover:text-gray-900"
        }`
      }
    >
      {label}
    </NavLink>
  );
}
