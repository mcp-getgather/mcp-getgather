import { useEffect, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import type { ExtractResult } from "./BrandForm";

interface ExtractResultsProps {
  extractResult?: ExtractResult;
}

function generateTable(dataArray: Record<string, unknown>[]) {
  if (!dataArray || dataArray.length === 0) return null;

  const headers = Object.keys(dataArray[0]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header} className="p-2 text-left">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {dataArray.map((rowData, rowIndex) => (
            <tr key={rowIndex}>
              {headers.map((header) => (
                <td key={`${rowIndex}-${header}`} className="p-2">
                  {String(rowData[header] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BundleContent({ bundle }: { bundle: ExtractResult["bundles"][number] }) {
  if (
    bundle.content === null ||
    bundle.content === undefined ||
    (typeof bundle.content === "string" && bundle.content.trim() === "")
  ) {
    return <div>No content available for this bundle.</div>;
  }

  if (
    bundle.parsed &&
    Array.isArray(bundle.content) &&
    bundle.content.length > 0 &&
    typeof bundle.content[0] === "object"
  ) {
    return generateTable(bundle.content as Record<string, unknown>[]);
  }

  if (bundle.parsed && typeof bundle.content === "object") {
    return (
      <div>
        <div className="text-muted-foreground mb-2 text-sm font-medium uppercase">
          Parsed data (non-tabular):
        </div>
        <pre className="bg-muted overflow-auto rounded-lg p-4">
          <code>{JSON.stringify(bundle.content, null, 2)}</code>
        </pre>
      </div>
    );
  }

  if (typeof bundle.content === "string") {
    try {
      const jsonObject = JSON.parse(bundle.content);
      return (
        <div>
          <div className="text-muted-foreground mb-2 text-sm font-medium uppercase">
            Raw JSON content:
          </div>
          <pre className="bg-muted overflow-auto rounded-lg p-4">
            <code>{JSON.stringify(jsonObject, null, 2)}</code>
          </pre>
        </div>
      );
    } catch {
      return (
        <div>
          <div className="text-muted-foreground mb-2 text-sm font-medium uppercase">
            Raw HTML/Text content:
          </div>
          <div
            className="overflow-auto rounded-lg border p-4"
            dangerouslySetInnerHTML={{ __html: bundle.content }}
          />
        </div>
      );
    }
  }

  if (typeof bundle.content === "object") {
    return (
      <div>
        <div className="text-muted-foreground mb-2 text-sm font-medium uppercase">
          Raw JSON content:
        </div>
        <pre className="bg-muted overflow-auto rounded-lg p-4">
          <code>{JSON.stringify(bundle.content, null, 2)}</code>
        </pre>
      </div>
    );
  }

  return <div>Content type not directly renderable.</div>;
}

export default function ExtractResults({ extractResult }: ExtractResultsProps) {
  const [activeTab, setActiveTab] = useState("0");

  useEffect(() => {
    setActiveTab("0");
  }, [extractResult]);

  if (!extractResult || !extractResult.bundles || extractResult.bundles.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Extract Results</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {extractResult.bundles.map((bundle, index) => (
              <TabsTrigger key={index} value={String(index)}>
                {bundle.name || `Bundle ${index + 1}`}
              </TabsTrigger>
            ))}
          </TabsList>
          {extractResult.bundles.map((bundle, index) => (
            <TabsContent key={index} value={String(index)}>
              <BundleContent bundle={bundle} />
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  );
}
