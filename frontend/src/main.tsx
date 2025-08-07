import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router";

import { Root } from "./components/root";
import { WelcomePage } from "./pages/welcome";
import { LiveViewPage } from "./pages/live-view";
import { ActivitiesPage } from "./pages/activities";
import { SettingsPage } from "./pages/settings";
import { NotFoundPage } from "./pages/not-found";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Root />}>
          <Route index element={<WelcomePage />} />
          <Route path="live-view" element={<LiveViewPage />} />
          <Route path="activities" element={<ActivitiesPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
