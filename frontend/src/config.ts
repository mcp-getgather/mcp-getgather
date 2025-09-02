import { createContext, useContext } from "react";
import type { StationConfig } from "./lib/api";

export const StationConfigContext = createContext<StationConfig>({ pages: [] });

export function useStationConfig() {
  return useContext(StationConfigContext);
}
