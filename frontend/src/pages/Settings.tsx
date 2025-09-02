import {
  Database,
  Download,
  Info,
  Monitor,
  Play,
  Radio,
  RotateCcw,
  Save,
  Trash,
  Wifi,
} from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Toggle } from "@/components/ui/toggle";

type DataSource = {
  id: string;
  name: string;
  connected: boolean;
  letter: string;
  bgClass: string;
  textClass: string;
};

const DATA_SOURCES = [
  {
    id: "amazon",
    name: "Amazon",
    connected: true,
    letter: "A",
    bgClass: "bg-orange-500",
    textClass: "text-white",
  },
  {
    id: "goodreads",
    name: "Goodreads",
    connected: true,
    letter: "G",
    bgClass: "bg-amber-500",
    textClass: "text-white",
  },
  {
    id: "doordash",
    name: "DoorDash",
    connected: false,
    letter: "D",
    bgClass: "bg-purple-500",
    textClass: "text-white",
  },
  {
    id: "bbc",
    name: "BBC",
    connected: true,
    letter: "B",
    bgClass: "bg-neutral-700",
    textClass: "text-white",
  },
  {
    id: "cnn",
    name: "CNN",
    connected: false,
    letter: "C",
    bgClass: "bg-red-500",
    textClass: "text-white",
  },
  {
    id: "zillow",
    name: "Zillow",
    connected: true,
    letter: "Z",
    bgClass: "bg-blue-800",
    textClass: "text-white",
  },
];

export default function Settings() {
  const [isRecordingEnabled, setIsRecordingEnabled] = useState(false);
  const [recordingDelay, setRecordingDelay] = useState(5);

  // TODO: get this from API
  const [dataSources, setDataSources] = useState<DataSource[]>(DATA_SOURCES);

  function toggleDataSource(id: string) {
    // TODO: integrate to API
    setDataSources((prev) =>
      prev.map((ds) => (ds.id === id ? { ...ds, connected: !ds.connected } : ds)),
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure GetGather Station to work with your preferred tools and data sources
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button size="sm" variant="outline" className="gap-2">
            <Download className="h-4 w-4" />
            Export Settings
          </Button>
          <Button size="sm" variant="outline">
            <RotateCcw className="h-4 w-4" />
            Reset to Defaults
          </Button>
          <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700">
            <Save className="h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </div>

      <div className="flex max-w-4xl flex-col gap-6">
        <Card className="border-border border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Radio className="h-4 w-4 text-red-500" />
                  <CardTitle className="text-lg font-semibold">Recording with rrweb</CardTitle>
                  <Info className="text-muted-foreground h-4 w-4" />
                </div>
              </div>
            </div>
            <CardDescription>Manage screen recording settings and playback options</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Enable Recording</div>
                <div className="text-muted-foreground text-sm">
                  Record user interactions and page changes
                </div>
              </div>
              <Toggle checked={isRecordingEnabled} onChange={setIsRecordingEnabled} />
            </div>

            <div className="pt-2">
              <div className="mb-4 font-medium">Recording Delay</div>
              <div className="px-1">
                <input
                  type="range"
                  min={0}
                  max={30}
                  value={recordingDelay}
                  onChange={(e) => setRecordingDelay(parseInt(e.target.value))}
                  className="w-full accent-slate-900"
                />
              </div>
              <div className="text-muted-foreground flex items-center justify-between text-sm">
                <span>0s</span>
                <span>{recordingDelay}s delay</span>
                <span>30s</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <Button className="gap-2 bg-indigo-600 hover:bg-indigo-700">
                <Play className="h-4 w-4" />
                Replay Recording
              </Button>
              <Button variant="outline">
                <Trash className="h-4 w-4" /> Clear Recordings
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Wifi className="h-4 w-4 text-blue-500" />
                  <CardTitle className="text-lg font-semibold">Proxy Service</CardTitle>
                  <Info className="text-muted-foreground h-4 w-4" />
                </div>
              </div>
            </div>
            <CardDescription>Enable proxy service for secure data access</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Proxy Service</div>
                <div className="text-muted-foreground text-sm">
                  Route requests through secure proxy
                </div>
              </div>
              <Toggle checked={isRecordingEnabled} onChange={setIsRecordingEnabled} />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-green-500" />
                  <CardTitle className="text-lg font-semibold">Interactive Live View</CardTitle>
                  <Info className="text-muted-foreground h-4 w-4" />
                </div>
              </div>
            </div>
            <CardDescription>Enable real-time interaction with the live view</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Interactive Mode</div>
                <div className="text-muted-foreground text-sm">
                  Allow clicking and interaction in live view
                </div>
              </div>
              <Toggle checked={isRecordingEnabled} onChange={setIsRecordingEnabled} />
            </div>
          </CardContent>
        </Card>

        <Card className="border-border border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-purple-500" />
                  <CardTitle className="text-lg font-semibold">Data Link Management</CardTitle>
                  <Info className="text-muted-foreground h-4 w-4" />
                </div>
              </div>
            </div>
            <CardDescription>
              Manage connected data sources and their access permissions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {dataSources.map((ds) => (
              <div
                key={ds.id}
                className="flex items-center justify-between rounded-xl border bg-white px-4 py-3 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-xl ${ds.bgClass}`}
                  >
                    <span className={`text-base font-semibold ${ds.textClass}`}>{ds.letter}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div>
                      <div className="leading-tight font-medium">{ds.name}</div>
                      <div className="text-muted-foreground text-sm">
                        {ds.connected ? "Connected" : "Disconnected"}
                      </div>
                    </div>
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-gray-100">
                      <Info className="h-3.5 w-3.5 text-gray-500" />
                    </span>
                  </div>
                </div>
                <Toggle checked={ds.connected} onChange={() => toggleDataSource(ds.id)} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
