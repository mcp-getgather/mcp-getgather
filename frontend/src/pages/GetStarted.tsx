import { Card, CardContent } from "@/components/ui/card";
import PageHeader from "@/components/PageHeader";
import { Sparkles, Zap, MessageCircle, Settings } from "lucide-react";

export default function GetStarted() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <PageHeader
        title="Welcome to GetGather Portal"
        description="Bridge the gap between AI agents and real-world data. Get started in 3 simple steps! See getgather operations in Live View and weigh in as needed."
        badge={{
          text: "AI-Powered Data Access",
          icon: Sparkles,
        }}
      />

      {/* Feature Cards */}
      <div className="grid md:grid-cols-3 gap-8">
        <Card className="text-center border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardContent className="pt-8 pb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <Zap className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-3">Setup</h3>
            <p className="text-gray-600">Quick set up for your MCP client</p>
          </CardContent>
        </Card>

        <Card className="text-center border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardContent className="pt-8 pb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <MessageCircle className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-3">Chat</h3>
            <p className="text-gray-600">Chat with your chosen client</p>
          </CardContent>
        </Card>

        <Card className="text-center border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardContent className="pt-8 pb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <Settings className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-3">
              Control
            </h3>
            <p className="text-gray-600">Configure getgather</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
