import { Button } from "@/components/ui/button";

export const HomePage = () => (
  <div className="flex min-h-screen flex-col items-center justify-center px-6">
    <h1 className="mb-8 text-4xl font-bold text-slate-900">Welcome to MCP GetGather!</h1>
    <Button asChild variant="default">
      <a href="/live">Show the live desktop</a>
    </Button>
  </div>
);
