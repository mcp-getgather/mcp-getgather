import { ArrowRight, Copy, Play, Settings, Sparkles, Zap } from "lucide-react";
import { useState } from "react";

import PageHeader from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const EXAMPLES = [
  {
    title: "Give me a list of purchases approaching their return expiration",
    description: "Analyzes your recent orders and identifies items with upcoming return deadlines",
    prompt: "Give me a list of purchases approaching their return expiration.",
  },
  {
    title: "Pull out my recent DoorDash orders",
    description: "Retrieves your latest food delivery orders with details and receipts",
    prompt: "Pull out my recent DoorDash orders.",
  },
  {
    title: "Get my reading list from Goodreads and share the links with John",
    description: "Fetches your Goodreads library and formats it for easy sharing",
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
    <div className="mx-auto max-w-6xl px-6 py-8">
      <PageHeader
        title="Welcome to GetGather Station"
        description={`Bridge the gap between AI agents and real-world data. Get started in 3 simple steps!\nSee getgather operations in Live View and weigh in as needed.`}
        badge={{
          text: "AI-Powered Data Access",
          icon: Sparkles,
        }}
      />

      {/* Feature Cards */}
      <div className="mx-auto mt-8 grid max-w-3xl justify-items-center gap-4 md:grid-cols-3">
        <Card className="border-0 bg-transparent text-center shadow-none transition-transform duration-200">
          <CardContent className="p-0">
            <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-orange-600 shadow-lg">
              <Zap className="h-8 w-8 text-white" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-slate-900">Setup</h3>
            <p className="text-slate-500">Quick set up for your MCP client</p>
          </CardContent>
        </Card>

        <Card className="border-0 bg-transparent text-center shadow-none transition-transform duration-200">
          <CardContent className="p-0">
            <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-purple-400 to-pink-600 shadow-lg">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-slate-900">Chat</h3>
            <p className="text-slate-500">Chat with your chosen client</p>
          </CardContent>
        </Card>

        <Card className="border-0 bg-transparent text-center shadow-none transition-transform duration-200">
          <CardContent className="p-0">
            <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-indigo-600 shadow-lg">
              <Settings className="h-8 w-8 text-white" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-slate-900">Control</h3>
            <p className="text-slate-500">Configure GetGather</p>
          </CardContent>
        </Card>
      </div>
      {/* Steps */}
      <div className="mt-12 grid gap-8 md:grid-cols-2">
        {/* Step 1 */}
        <Card className="border-0 py-0 shadow-lg">
          <CardContent className="p-6">
            <div className="text-md mb-4 font-semibold">Step 1</div>
            <div className="mb-2 text-2xl font-bold text-slate-900">Quick Setup</div>
            <p className="mb-6 text-slate-600">
              Transform your AI workflow in under 5 minutes. GetGather Station seamlessly integrates
              with your existing tools to provide real-time data access capabilities.
            </p>
            <div className="mb-6 space-y-4 rounded-lg bg-yellow-50 p-4">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-yellow-600"></div>
                <span className="text-md font-semibold">Setup process:</span>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs text-white">
                  1
                </div>
                <div className="text-slate-700">Configure API endpoint and authentication</div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-xs text-white">
                  2
                </div>
                <div className="text-slate-700">Connect your data sources and test connection</div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border bg-white p-4">
                <div className="flex items-center justify-between">
                  <div className="mb-2 text-sm font-bold text-slate-700">Claude Configuration</div>
                  <div className="mb-2 rounded-sm bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-700">
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
                  <div className="mb-2 text-sm font-bold text-slate-700">Cursor Configuration</div>
                  <div className="mb-2 rounded-sm bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-700">
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
        <Card className="border-0 py-0 shadow-lg">
          <CardContent className="p-6">
            <div className="text-md mb-4 font-semibold">Step 2</div>
            <div className="mb-2 text-2xl font-bold text-slate-900">Try out in your client</div>
            <p className="mb-6 text-slate-600">Copy these examples and see the magic happen.</p>
            <div className="space-y-4">
              {EXAMPLES.map((ex, idx) => (
                <div key={idx} className="rounded-lg border p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="font-medium text-slate-900">{ex.title}</div>
                      <div className="mt-1 text-sm text-slate-600">{ex.description}</div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Button
                        variant="outline"
                        onClick={() => copyPrompt(ex.prompt, idx)}
                        className="min-w-[90px]"
                      >
                        <Copy className="h-4 w-4" /> {copiedIndex === idx ? "Copied" : "Copy"}
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
          <div className="mb-3 text-2xl font-bold md:text-3xl">Ready to see it in action?</div>
          <p className="mb-6 opacity-90">
            Watch your agent work in real-time and see exactly how GetGather Station transforms data
            access challenges into seamless solutions.
          </p>
          <Button asChild size="lg" className="bg-white text-indigo-700 hover:bg-white/90">
            <a href="/live-view">
              <Play className="mr-2 h-4 w-4" /> Launch Live View{" "}
              <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}
