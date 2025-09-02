import { createElement, StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";
import Layout from "./components/Layout";
import { StationConfigContext, useStationConfig } from "./config";
import "./index.css";
import { ApiService, type StationConfig } from "./lib/api";
import Activities from "./pages/Activities";
import GetStarted from "./pages/GetStarted";
import Home from "./pages/Home";
import Link from "./pages/Link";
import LiveView from "./pages/LiveView";
import McpDocs from "./pages/MCPDocs";
import NotFound from "./pages/NotFound";
import Replay from "./pages/Replay";
import Start from "./pages/Start";

const PAGES = {
  GetStarted: GetStarted,
  LiveView: LiveView,
  Activities: Activities,
  McpDocs: McpDocs,
  Replay: Replay,
};

function StationConfigProvider({ children }: { children: React.ReactNode }) {
  const [stationConfig, setStationConfig] = useState<StationConfig>({
    pages: [],
  });
  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStationConfig = async () => {
      try {
        const data = await ApiService.getStationConfig();
        setStationConfig(data);
      } catch (error) {
        setConfigError(
          error instanceof Error ? error.message : "An error occurred",
        );
      }
    };
    fetchStationConfig();
  }, []);

  if (configError) {
    return <div>Error loading station configuration: {configError}</div>;
  }

  return (
    <StationConfigContext.Provider value={stationConfig}>
      {children}
    </StationConfigContext.Provider>
  );
}

export default function App() {
  const { pages } = useStationConfig();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/home" element={<Home />} />
        <Route path="/link/:linkId" element={<Link />} />
        <Route path="/start/:brandId" element={<Start />} />
        <Route path="/" element={<Layout />}>
          {pages.map((page) => (
            <Route
              path={page.path}
              element={createElement(PAGES[page.name as keyof typeof PAGES])}
            />
          ))}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <StationConfigProvider>
      <App />
    </StationConfigProvider>
  </StrictMode>,
);
