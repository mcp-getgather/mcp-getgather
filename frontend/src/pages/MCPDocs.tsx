import { Wrench } from "lucide-react";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";

import { $api } from "@/lib/api";

type MCPDoc = {
  name: string;
  type: "brand" | "category" | "all";
  route: string;
  tools: { name: string; description: string }[];
};

export default function McpDocs() {
  return (
    <ErrorBoundary fallback={<div>Error loading MCP docs</div>}>
      <Suspense fallback={<div>Loading MCP docs...</div>}>
        <MCPDocsContent />
      </Suspense>
    </ErrorBoundary>
  );
}

function MCPDocsContent() {
  const { data } = $api.useSuspenseQuery("get", "/docs-mcp");

  const groupedServers = data.reduce(
    (acc, server) => {
      if (!acc[server.type]) {
        acc[server.type] = [];
      }
      acc[server.type]?.push(server);
      return acc;
    },
    {} as Record<string, MCPDoc[]>,
  );

  const getTypeTitle = (type: string) => {
    switch (type) {
      case "brand":
        return "Brand Specific Servers";
      case "category":
        return "Category Servers";
      case "all":
        return "Everything Server";
      default:
        return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  const getTypeDescription = (type: string) => {
    switch (type) {
      case "brand":
        return "Individual brand-specific MCP servers";
      case "category":
        return "Grouped brands and tools by category";
      case "all":
        return "Every brand and tool";
      default:
        return `${type} servers`;
    }
  };

  return (
    <div className="mx-auto max-w-7xl pb-12">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-slate-800">MCP Servers</h1>
        <p className="text-slate-600">Explore available MCP servers and their tools</p>
      </div>

      {Object.keys(groupedServers).length === 0 ? (
        <div className="py-12 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
            <Wrench className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="mb-2 text-lg font-medium text-slate-800">No MCP servers found</h3>
          <p className="text-slate-600">MCP servers will appear here once they are configured.</p>
        </div>
      ) : (
        <div className="space-y-12">
          {Object.entries(groupedServers)
            .sort(([a], [b]) => {
              const order = ["all", "category", "brand"];
              return order.indexOf(a) - order.indexOf(b);
            })
            .map(([type, typeServers]) => (
              <section key={type} className="space-y-6">
                <div className="border-b border-slate-200 pb-4">
                  <h2 className="mb-1 text-2xl font-bold text-slate-800">{getTypeTitle(type)}</h2>
                  <p className="text-slate-600">{getTypeDescription(type)}</p>
                  <span className="mt-2 inline-block text-sm text-slate-500">
                    {typeServers.length} server
                    {typeServers.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {typeServers.map((server, serverIndex) => (
                    <ServerCard key={`${server.name}-${serverIndex}`} server={server} />
                  ))}
                </div>
              </section>
            ))}
        </div>
      )}
    </div>
  );
}

function ServerCard({ server }: { server: MCPDoc }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-md transition-shadow hover:shadow-lg">
      <div className="p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-xl font-semibold text-slate-800 capitalize">{server.name}</h3>
        </div>

        <div className="mb-4">
          <div className="mb-3 flex items-center gap-2">
            <Wrench className="h-4 w-4 text-slate-500" />
            <h4 className="text-sm font-medium text-slate-700">Available Tools</h4>
            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
              {server.tools.length}
            </span>
          </div>
          <div className="max-h-40 overflow-y-auto">
            <ul className="space-y-1">
              {server.tools.map((tool, toolIndex) => (
                <li
                  key={`${tool.name}-${toolIndex}`}
                  className="flex items-center gap-2 text-sm text-slate-600"
                >
                  <div className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-indigo-400"></div>
                  <span className="font-mono">{tool.name}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
