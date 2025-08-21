import { ExternalLink, Wrench } from "lucide-react";
import { useEffect, useState } from "react";

type MCPDoc = {
  name: string;
  type: "brand" | "category" | "all";
  route: string;
  tools: { name: string; route: string; description: string }[];
};

export default function McpDocs() {
  const [servers, setServers] = useState<MCPDoc[]>([]);
  useEffect(() => {
    fetch("/api/mcp-docs")
      .then((res) => res.json())
      .then((data) => setServers(data));
  }, []);

  const groupedServers = servers.reduce(
    (acc, server) => {
      if (!acc[server.type]) {
        acc[server.type] = [];
      }
      acc[server.type].push(server);
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
    <div className="max-w-7xl mx-auto pb-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-800 mb-2">MCP Servers</h1>
        <p className="text-slate-600">
          Explore available MCP servers and their tools
        </p>
      </div>

      {Object.keys(groupedServers).length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Wrench className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-800 mb-2">
            No MCP servers found
          </h3>
          <p className="text-slate-600">
            MCP servers will appear here once they are configured.
          </p>
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
                  <h2 className="text-2xl font-bold text-slate-800 mb-1">
                    {getTypeTitle(type)}
                  </h2>
                  <p className="text-slate-600">{getTypeDescription(type)}</p>
                  <span className="inline-block mt-2 text-sm text-slate-500">
                    {typeServers.length} server
                    {typeServers.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {typeServers.map((server, serverIndex) => (
                    <ServerCard
                      key={`${server.name}-${serverIndex}`}
                      server={server}
                    />
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
    <div className="bg-white rounded-lg shadow-md border border-slate-200 overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-slate-800 capitalize">
            {server.name}
          </h3>
          <InspectorLink route={server.route} />
        </div>

        <div className="mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Wrench className="w-4 h-4 text-slate-500" />
            <h4 className="text-sm font-medium text-slate-700">
              Available Tools
            </h4>
            <span className="bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded-full">
              {server.tools.length}
            </span>
          </div>
          <div className="max-h-40 overflow-y-auto">
            <ul className="space-y-1">
              {server.tools.map((tool, toolIndex) => (
                <li
                  key={`${tool.name}-${toolIndex}`}
                  className="text-sm text-slate-600 flex items-center gap-2"
                >
                  <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full flex-shrink-0"></div>
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

function InspectorLink({ route }: { route: string }) {
  const baseUrl =
    "/inspector/?MCP_PROXY_AUTH_TOKEN=getgather&transport=streamable-http";
  return (
    <a
      href={`${baseUrl}&serverUrl=http://localhost:23456${route}/`}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-100 text-indigo-700 text-sm font-medium rounded-md hover:bg-indigo-200 transition-colors"
    >
      Inspector
      <ExternalLink className="w-3 h-3" />
    </a>
  );
}
