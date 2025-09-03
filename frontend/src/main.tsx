import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";

import type { paths } from "@generated/api";

import Layout from "./components/Layout";
import "./index.css";
import Activities from "./pages/Activities";
import GetStarted from "./pages/GetStarted";
import Home from "./pages/Home";
import Link from "./pages/Link";
import LiveView from "./pages/LiveView";
import McpDocs from "./pages/MCPDocs";
import NotFound from "./pages/NotFound";
import { ReplayPage } from "./pages/Replay";
import Start from "./pages/Start";

const fetchClient = createFetchClient<paths>({ baseUrl: "/api" });
export const apiClient = createClient(fetchClient);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={new QueryClient()}>
      <BrowserRouter>
        <Routes>
          <Route path="/home" element={<Home />} />
          <Route path="/link/:linkId" element={<Link />} />
          <Route path="/start/:brandId" element={<Start />} />
          <Route path="/" element={<Layout />}>
            <Route path="" element={<GetStarted />} />
            <Route path="live-view" element={<LiveView />} />
            <Route path="activities" element={<Activities />} />
            <Route path="replay" element={<ReplayPage />} />
            <Route path="/docs-mcp" element={<McpDocs />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
