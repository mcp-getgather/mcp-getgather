import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import Layout from "./components/Layout";
import "./index.css";
import Activities from "./pages/Activities";
import GetStarted from "./pages/GetStarted";
import Home from "./pages/Home";
import Link from "./pages/Link";
import LiveView from "./pages/LiveView";
import McpDocs from "./pages/MCPDocs";
import { ReplayPage } from "./pages/Replay";
import Settings from "./pages/Settings";
import Start from "./pages/Start";
import NotFound from "./pages/NotFound";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/link/:linkId" element={<Link />} />
        <Route path="/start/:brandId" element={<Start />} />
        <Route path="/" element={<Layout />}>
          <Route path="" element={<GetStarted />} />
          <Route path="live-view" element={<LiveView />} />
          <Route path="activities" element={<Activities />} />
          <Route path="settings" element={<Settings />} />
          <Route path="replay" element={<ReplayPage />} />
          <Route path="/mcp-docs" element={<McpDocs />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
