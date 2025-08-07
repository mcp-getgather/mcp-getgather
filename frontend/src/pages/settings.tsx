import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Settings as SettingsIcon, Shield, Bell, Database } from "lucide-react";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Configure your GetGather Studio preferences and manage your account.
        </p>
      </div>

      {/* Settings Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <SettingsIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <CardTitle>General Settings</CardTitle>
                <CardDescription>Basic configuration options</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Auto-refresh dashboard</span>
              <Badge variant="secondary">Enabled</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Theme</span>
              <Badge variant="outline">Light</Badge>
            </div>
            <Button variant="outline" size="sm">
              Configure
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <CardTitle>Security</CardTitle>
                <CardDescription>
                  Authentication and access control
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Two-factor authentication</span>
              <Badge variant="default">Active</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Session timeout</span>
              <Badge variant="outline">24 hours</Badge>
            </div>
            <Button variant="outline" size="sm">
              Manage
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <Bell className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>
                  Alert preferences and channels
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Email notifications</span>
              <Badge variant="secondary">Enabled</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Browser notifications</span>
              <Badge variant="outline">Disabled</Badge>
            </div>
            <Button variant="outline" size="sm">
              Update
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                <Database className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <CardTitle>Data & Storage</CardTitle>
                <CardDescription>
                  Manage your data and storage preferences
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between items-center">
              <span>Data retention</span>
              <Badge variant="outline">30 days</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>Export format</span>
              <Badge variant="outline">JSON</Badge>
            </div>
            <Button variant="outline" size="sm">
              Export Data
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
