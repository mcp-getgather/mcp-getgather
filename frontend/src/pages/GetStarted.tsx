import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import PageHeader from "@/components/PageHeader";
import { Sparkles, Zap, Settings, Play, Copy, ArrowRight } from "lucide-react";

const EXAMPLES = [
  {
    title: "Give me a list of purchases approaching their return expiration",
    description:
      "Analyzes your recent orders and identifies items with upcoming return deadlines",
    prompt: "Give me a list of purchases approaching their return expiration.",
  },
  {
    title: "Pull out my recent DoorDash orders",
    description:
      "Retrieves your latest food delivery orders with details and receipts",
    prompt: "Pull out my recent DoorDash orders.",
  },
  {
    title: "Get my reading list from Goodreads and share the links with John",
    description:
      "Fetches your Goodreads library and formats it for easy sharing",
    prompt:
      "Get my reading list (read and currently reading) from Goodreads and share the links with John.",
  },
];

export default function GetStarted() {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyPrompt = async (text: string, idx: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(idx);
      window.setTimeout(() => setCopiedIndex(null), 1500);
    } catch {
      // Ignore copy errors
    }
  };
  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <PageHeader
        title="Welcome to GetGather Station"
        description={`Bridge the gap between AI agents and real-world data. Get started in 3 simple steps!\nSee getgather operations in Live View and weigh in as needed.`}
        badge={{
          text: "AI-Powered Data Access",
          icon: Sparkles,
        }}
      />

      {/* Feature Cards */}
      <div className="grid md:grid-cols-3 gap-4 justify-items-center mt-8 max-w-3xl mx-auto">
        <Card className="text-center bg-transparent border-0 shadow-none transition-transform duration-200">
          <CardContent className="p-0">
            <div className="w-20 h-20 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Setup</h3>
            <p className="text-slate-500">Quick set up for your MCP client</p>
          </CardContent>
        </Card>

        <Card className="text-center bg-transparent border-0 shadow-none transition-transform duration-200">
          <CardContent className="p-0">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">Chat</h3>
            <p className="text-slate-500">Chat with your chosen client</p>
          </CardContent>
        </Card>

        <Card className="text-center bg-transparent border-0 shadow-none transition-transform duration-200">
          <CardContent className="p-0">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-5 shadow-lg">
              <Settings className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-2">
              Control
            </h3>
            <p className="text-slate-500">Configure GetGather</p>
          </CardContent>
        </Card>
      </div>
      {/* Steps */}
      <div className="grid md:grid-cols-2 gap-8 mt-12">
        {/* Step 1 */}
        <Card className="border-0 shadow-lg py-0">
          <CardContent className="p-6">
            <div className="mb-4 text-md font-semibold">Step 1</div>
            <div className="text-2xl font-bold text-slate-900 mb-2">
              Quick Setup
            </div>
            <p className="text-slate-600 mb-6">
              Transform your AI workflow in under 5 minutes. GetGather Station
              seamlessly integrates with your existing tools to provide
              real-time data access capabilities.
            </p>
            <div className="space-y-4 bg-yellow-50 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-yellow-600 rounded-full"></div>
                <span className="text-md font-semibold">Setup process:</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs mt-0.5">
                  1
                </div>
                <div className="text-slate-700">
                  Configure API endpoint and authentication
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs mt-0.5">
                  2
                </div>
                <div className="text-slate-700">
                  Connect your data sources and test connection
                </div>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-slate-700 mb-2">
                    Claude Configuration
                  </div>
                  <div className="text-xs font-semibold text-indigo-700 mb-2 bg-indigo-100 rounded-sm px-2 py-1">
                    CLAUDE
                  </div>
                </div>
                <Button asChild variant="outline" className="w-full">
                  <a href="https://github.com/mcp-getgather/mcp-getgather?tab=readme-ov-file#get-gather">
                    Setup Guide
                  </a>
                </Button>
              </div>
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-bold text-slate-700 mb-2">
                    Cursor Configuration
                  </div>
                  <div className="text-xs font-semibold text-indigo-700 mb-2 bg-indigo-100 rounded-sm px-2 py-1">
                    CURSOR
                  </div>
                </div>

                <Button asChild variant="outline" className="w-full">
                  <a href="cursor://anysphere.cursor-deeplink/mcp/install?name=getgather&config=eyJ1cmwiOiJodHRwOi8vMTI3LjAuMC4xOjIzNDU2L21jcCJ9">
                    Install Now
                  </a>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Step 2 */}
        <Card className="border-0 shadow-lg py-0">
          <CardContent className="p-6">
            <div className="mb-4 text-md font-semibold">Step 2</div>
            <div className="text-2xl font-bold text-slate-900 mb-2">
              Try out in your client
            </div>
            <p className="text-slate-600 mb-6">
              Copy these examples and see the magic happen.
            </p>
            <div className="space-y-4">
              {EXAMPLES.map((ex, idx) => (
                <div key={idx} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="font-medium text-slate-900">
                        {ex.title}
                      </div>
                      <div className="text-sm text-slate-600 mt-1">
                        {ex.description}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        variant="outline"
                        onClick={() => copyPrompt(ex.prompt, idx)}
                        className="min-w-[90px]"
                      >
                        <Copy className="w-4 h-4" />{" "}
                        {copiedIndex === idx ? "Copied" : "Copy"}
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Step 3 */}
      <div className="mt-10">
        <div className="rounded-2xl bg-gradient-to-r from-indigo-500 to-violet-600 p-8 text-center text-white shadow-lg">
          <div className="text-2xl md:text-3xl font-bold mb-3">
            Ready to see it in action?
          </div>
          <p className="opacity-90 mb-6">
            Watch your agent work in real-time and see exactly how GetGather
            Station transforms data access challenges into seamless solutions.
          </p>
          <Button
            asChild
            size="lg"
            className="bg-white text-indigo-700 hover:bg-white/90"
          >
            <a href="/live-view">
              <Play className="w-4 h-4 mr-2" /> Launch Live View{" "}
              <ArrowRight className="w-4 h-4 ml-2" />
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}
