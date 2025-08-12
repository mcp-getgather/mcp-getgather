import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useEffect, useState } from "react";
import {
  Info,
  Download,
  Radio,
  Play,
  Trash,
  RotateCcw,
  Save,
  Wifi,
  Monitor,
  Database,
} from "lucide-react";
import { Toggle } from "@/components/ui/toggle";
import apiService, { type BrandState } from "@/lib/api-service";

function BrandIcon({ brandId, size = 40 }: { brandId: string; size?: number }) {
  const [src, setSrc] = useState(`/static/assets/logos/${brandId}.svg`);

  function handleError() {
    if (src.endsWith(".svg")) {
      setSrc(`/static/assets/logos/${brandId}.png`);
      return;
    }
    if (src.endsWith(".png")) {
      setSrc("/static/assets/logos/default.svg");
    }
  }

  return (
    <img
      src={src}
      alt={brandId}
      width={size}
      height={size}
      loading="lazy"
      onError={handleError}
      className="h-10 w-10 rounded-xl bg-gray-50 object-contain p-1"
    />
  );
}

export default function Settings() {
  const [isRecordingEnabled, setIsRecordingEnabled] = useState(false);
  const [recordingDelay, setRecordingDelay] = useState(5);

  const [brands, setBrands] = useState<BrandState[]>([]);

  function toggleBrandEnabled(brand_id: string) {
    const brand = brands.find((b) => b.brand_id === brand_id);
    if (!brand) {
      return;
    }

    setBrands(
      brands.map((b) =>
        b.brand_id === brand_id ? { ...b, enabled: !b.enabled } : b,
      ),
    );
    apiService
      .updateBrandEnabled(brand_id, !brand.enabled)
      .then(() => {})
      .catch((error) => {
        console.error(error);
        setBrands(
          brands.map((b) =>
            b.brand_id === brand_id ? { ...b, enabled: !b.enabled } : b,
          ),
        );
      });
  }

  useEffect(() => {
    apiService.fetchBrands().then((result) => {
      setBrands(result);
    });
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Configure GetGather Portal to work with your preferred tools and
            data sources
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

      <div className="flex flex-col gap-6 max-w-4xl">
        <Card className="border border-border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Radio className="h-4 w-4 text-red-500" />
                  <CardTitle className="text-lg font-semibold">
                    Recording with rrweb
                  </CardTitle>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            </div>
            <CardDescription>
              Manage screen recording settings and playback options
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Enable Recording</div>
                <div className="text-sm text-muted-foreground">
                  Record user interactions and page changes
                </div>
              </div>
              <Toggle
                checked={isRecordingEnabled}
                onChange={setIsRecordingEnabled}
              />
            </div>

            <div className="pt-2">
              <div className="font-medium mb-4">Recording Delay</div>
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
              <div className="flex items-center justify-between text-sm text-muted-foreground">
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

        <Card className="border border-border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Wifi className="h-4 w-4 text-blue-500" />
                  <CardTitle className="text-lg font-semibold">
                    Proxy Service
                  </CardTitle>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            </div>
            <CardDescription>
              Enable proxy service for secure data access
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Proxy Service</div>
                <div className="text-sm text-muted-foreground">
                  Route requests through secure proxy
                </div>
              </div>
              <Toggle
                checked={isRecordingEnabled}
                onChange={setIsRecordingEnabled}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Monitor className="h-4 w-4 text-green-500" />
                  <CardTitle className="text-lg font-semibold">
                    Interactive Live View
                  </CardTitle>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            </div>
            <CardDescription>
              Enable real-time interaction with the live view
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Interactive Mode</div>
                <div className="text-sm text-muted-foreground">
                  Allow clicking and interaction in live view
                </div>
              </div>
              <Toggle
                checked={isRecordingEnabled}
                onChange={setIsRecordingEnabled}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-purple-500" />
                  <CardTitle className="text-lg font-semibold">
                    Data Link Management
                  </CardTitle>
                  <Info className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            </div>
            <CardDescription>
              Manage connected data sources and their access permissions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {brands.map((brand) => (
              <div
                key={brand.brand_id}
                className="flex items-center justify-between rounded-xl border bg-white px-4 py-3 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <BrandIcon brandId={brand.brand_id} />
                  <div className="flex items-center gap-2">
                    <div>
                      <div className="font-medium leading-tight">
                        {brand.name}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {brand.is_connected ? "Connected" : "Disconnected"}
                      </div>
                    </div>
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-gray-100">
                      <Info className="h-3.5 w-3.5 text-gray-500" />
                    </span>
                  </div>
                </div>
                <Toggle
                  checked={brand.enabled}
                  onChange={() => toggleBrandEnabled(brand.brand_id)}
                />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
