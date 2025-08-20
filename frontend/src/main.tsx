import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router";
import Layout from "./components/Layout";
import GetStarted from "./pages/GetStarted";
import Activities from "./pages/Activities";
import LiveView from "./pages/LiveView";
import Settings from "./pages/Settings";
import "./index.css";
import Home from "./pages/Home";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/" element={<Layout />}>
          <Route path="welcome" element={<GetStarted />} />
          <Route path="live-view" element={<LiveView />} />
          <Route path="activities" element={<Activities />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
