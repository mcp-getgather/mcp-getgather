import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";

import Layout from "./components/Layout";
import "./index.css";
import { activitiesEnabled, liveViewEnabled, replayEnabled } from "./lib/config";
import Activities from "./pages/Activities";
import GetStarted from "./pages/GetStarted";
import Link from "./pages/Link";
import LiveView from "./pages/LiveView";
import McpDocs from "./pages/MCPDocs";
import NotFound from "./pages/NotFound";
import { ReplayPage } from "./pages/Replay";

console.debug(`MULTI_USER_ENABLED: ${import.meta.env.MULTI_USER_ENABLED}`);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={new QueryClient()}>
      <BrowserRouter>
        <Routes>
          <Route path="/link/:linkId" element={<Link />} />
          <Route path="/" element={<Layout />}>
            <Route path="" element={<GetStarted />} />
            {liveViewEnabled() && <Route path="live-view" element={<LiveView />} />}
            {activitiesEnabled() && <Route path="activities" element={<Activities />} />}
            {replayEnabled() && <Route path="replay" element={<ReplayPage />} />}
            <Route path="/docs-mcp" element={<McpDocs />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
