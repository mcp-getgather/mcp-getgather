import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";

import Layout from "./components/Layout";
import "./index.css";
import { liveViewEnabled } from "./lib/config";
import GetStarted from "./pages/GetStarted";
import LiveView from "./pages/LiveView";
import McpDocs from "./pages/MCPDocs";
import NotFound from "./pages/NotFound";

console.debug(`MULTI_USER_ENABLED: ${import.meta.env.MULTI_USER_ENABLED}`);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={new QueryClient()}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route path="" element={<GetStarted />} />
            {liveViewEnabled() && <Route path="live-view" element={<LiveView />} />}
            <Route path="/docs-mcp" element={<McpDocs />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
