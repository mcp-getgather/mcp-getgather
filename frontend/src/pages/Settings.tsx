import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/PageHeader";
import { Settings as SettingsIcon, Database, Shield, Bell } from "lucide-react";

export default function Settings() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <PageHeader
        title="Settings"
        description="Configure your GetGather Studio preferences"
        badge={{
          text: "Configuration",
          icon: SettingsIcon,
        }}
      />

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <CardTitle>Data Sources</CardTitle>
                <CardDescription>
                  Manage your connected data sources
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Badge variant="outline" className="mb-3">
              3 Connected
            </Badge>
            <Button variant="outline" className="w-full">
              Manage Sources
            </Button>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <CardTitle>Security</CardTitle>
                <CardDescription>
                  Configure authentication and access
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Badge variant="outline" className="mb-3">
              Secured
            </Badge>
            <Button variant="outline" className="w-full">
              Security Settings
            </Button>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <Bell className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>
                  Control your notification preferences
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Badge variant="outline" className="mb-3">
              Enabled
            </Badge>
            <Button variant="outline" className="w-full">
              Notification Settings
            </Button>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <SettingsIcon className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <CardTitle>General</CardTitle>
                <CardDescription>Basic application preferences</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Button variant="outline" className="w-full">
              General Settings
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
