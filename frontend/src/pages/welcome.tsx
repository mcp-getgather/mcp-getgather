import { Zap, Sparkles, Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function WelcomePage() {
  return (
    <div className="text-center space-y-8">
      {/* Hero Badge */}
      <div className="flex justify-center">
        <Badge
          variant="secondary"
          className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 text-sm font-medium border-0"
        >
          <Sparkles className="w-4 h-4 mr-2" />
          AI-Powered Data Access
        </Badge>
      </div>

      {/* Main Heading */}
      <div className="space-y-4">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
          Welcome to GetGather Studio
        </h1>

        <div className="text-lg text-gray-600 max-w-3xl mx-auto">
          <p>
            Bridge the gap between AI agents and real-world data.{" "}
            <span className="text-blue-600 font-semibold">
              Get started in 3 simple steps!
            </span>
          </p>
          <p className="mt-2">
            See getgather operations in Live View and weigh in as needed
          </p>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid md:grid-cols-3 gap-6 mt-12 max-w-4xl mx-auto">
        {/* Setup Card */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 bg-white/70 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-xl font-semibold text-gray-900">
              Setup
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <CardDescription className="text-gray-600">
              Quick set up for your MCP client
            </CardDescription>
          </CardContent>
        </Card>

        {/* Chat Card */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 bg-white/70 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-pink-400 to-purple-500 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-xl font-semibold text-gray-900">
              Chat
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <CardDescription className="text-gray-600">
              Chat with your chosen client
            </CardDescription>
          </CardContent>
        </Card>

        {/* Control Card */}
        <Card className="group hover:shadow-lg transition-all duration-300 border-0 bg-white/70 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
              <Rocket className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-xl font-semibold text-gray-900">
              Control
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <CardDescription className="text-gray-600">
              Configure getgather
            </CardDescription>
          </CardContent>
        </Card>
      </div>

      {/* Call to Action */}
      <div className="mt-12 space-y-4">
        <Button
          size="lg"
          className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-8 py-3"
        >
          Get Started Now
        </Button>
        <p className="text-sm text-gray-500">
          No credit card required • Free forever plan available
        </p>
      </div>
    </div>
  );
}
