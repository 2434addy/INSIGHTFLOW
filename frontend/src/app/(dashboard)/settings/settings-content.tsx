"use client";

import { PageHeader } from "@/components/common/page-header";
import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Building2,
  Globe,
  Key,
  Link2,
  Plug,
  Shield,
  User,
  Users,
} from "lucide-react";
import { useState } from "react";

type SettingsTab =
  | "general"
  | "team"
  | "integrations"
  | "api"
  | "security";

const TABS: { id: SettingsTab; label: string; icon: typeof User }[] = [
  { id: "general", label: "General", icon: Building2 },
  { id: "team", label: "Team", icon: Users },
  { id: "integrations", label: "Integrations", icon: Plug },
  { id: "api", label: "API Keys", icon: Key },
  { id: "security", label: "Security", icon: Shield },
];

const INTEGRATIONS = [
  {
    name: "Meta Ads",
    description: "Connect your Meta Business accounts",
    icon: Globe,
    connected: true,
    accounts: 3,
  },
  {
    name: "Google Ads",
    description: "Connect your Google Ads accounts",
    icon: Globe,
    connected: true,
    accounts: 2,
  },
  {
    name: "Google Analytics 4",
    description: "Connect your GA4 properties",
    icon: Globe,
    connected: false,
    accounts: 0,
  },
  {
    name: "Shopify",
    description: "Connect your Shopify stores",
    icon: Globe,
    connected: false,
    accounts: 0,
  },
];

export function SettingsContent() {
  const [activeTab, setActiveTab] = useState<SettingsTab>("general");

  return (
    <>
      <Topbar title="Settings" />
      <div className="p-6">
        <PageHeader
          title="Settings"
          description="Manage your workspace, team, and integrations"
        />

        <div className="mt-6 flex gap-6">
          {/* Tab Navigation */}
          <nav className="w-56 shrink-0 space-y-1" aria-label="Settings tabs">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
                aria-current={activeTab === tab.id ? "true" : undefined}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Tab Content */}
          <div className="flex-1 space-y-6">
            {activeTab === "general" && <GeneralSettings />}
            {activeTab === "team" && <TeamSettings />}
            {activeTab === "integrations" && <IntegrationSettings />}
            {activeTab === "api" && <APISettings />}
            {activeTab === "security" && <SecuritySettings />}
          </div>
        </div>
      </div>
    </>
  );
}

function GeneralSettings() {
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Workspace</CardTitle>
          <CardDescription>
            Manage your workspace settings and preferences
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label
              htmlFor="workspace-name"
              className="block text-sm font-medium text-gray-700"
            >
              Workspace Name
            </label>
            <input
              id="workspace-name"
              type="text"
              defaultValue="Acme Marketing Agency"
              className="mt-1 block w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label
              htmlFor="workspace-slug"
              className="block text-sm font-medium text-gray-700"
            >
              Workspace URL
            </label>
            <div className="mt-1 flex max-w-md items-center">
              <span className="rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-500">
                insightflow.app/
              </span>
              <input
                id="workspace-slug"
                type="text"
                defaultValue="acme-agency"
                className="block w-full rounded-r-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="pt-2">
            <Button>Save Changes</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Report Defaults</CardTitle>
          <CardDescription>
            Default settings for new report generation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label
              htmlFor="default-tone"
              className="block text-sm font-medium text-gray-700"
            >
              Default Tone
            </label>
            <select
              id="default-tone"
              defaultValue="executive"
              className="mt-1 block w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="executive">Executive (concise)</option>
              <option value="detailed">Detailed (thorough)</option>
              <option value="casual">Casual (accessible)</option>
            </select>
          </div>
          <div>
            <label
              htmlFor="default-comparison"
              className="block text-sm font-medium text-gray-700"
            >
              Default Comparison Period
            </label>
            <select
              id="default-comparison"
              defaultValue="previous_period"
              className="mt-1 block w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="previous_period">Previous period</option>
              <option value="previous_year">Same period last year</option>
            </select>
          </div>
          <div className="pt-2">
            <Button>Save Defaults</Button>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

function TeamSettings() {
  const members = [
    { name: "Jane Smith", email: "jane@acme.agency", role: "Owner" },
    { name: "Mike Johnson", email: "mike@acme.agency", role: "Admin" },
    { name: "Sarah Lee", email: "sarah@acme.agency", role: "Member" },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Team Members</CardTitle>
            <CardDescription>
              Manage who has access to your workspace
            </CardDescription>
          </div>
          <Button>
            <User className="h-4 w-4" />
            Invite Member
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-gray-100">
          {members.map((member) => (
            <div
              key={member.email}
              className="flex items-center justify-between py-3"
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-sm font-medium text-blue-700">
                  {member.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {member.name}
                  </p>
                  <p className="text-sm text-gray-500">{member.email}</p>
                </div>
              </div>
              <Badge variant={member.role === "Owner" ? "default" : "neutral"}>
                {member.role}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function IntegrationSettings() {
  return (
    <div className="space-y-4">
      {INTEGRATIONS.map((integration) => (
        <Card key={integration.name}>
          <CardContent className="flex items-center justify-between p-4">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-gray-100 p-2.5">
                <integration.icon className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">
                  {integration.name}
                </h3>
                <p className="text-sm text-gray-500">
                  {integration.description}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {integration.connected && (
                <span className="text-sm text-gray-500">
                  {integration.accounts} account
                  {integration.accounts !== 1 ? "s" : ""}
                </span>
              )}
              {integration.connected ? (
                <Badge variant="success">Connected</Badge>
              ) : (
                <Button variant="outline" size="sm">
                  <Link2 className="h-4 w-4" />
                  Connect
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function APISettings() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>API Keys</CardTitle>
        <CardDescription>
          Manage API keys for programmatic access to InsightFlow
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">Production Key</p>
              <p className="font-mono text-sm text-gray-500">
                isf_prod_****************************3a7f
              </p>
            </div>
            <Button variant="outline" size="sm">
              Regenerate
            </Button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Created Jan 15, 2026 | Last used Mar 10, 2026
          </p>
        </div>
        <Button variant="outline">
          <Key className="h-4 w-4" />
          Create New Key
        </Button>
      </CardContent>
    </Card>
  );
}

function SecuritySettings() {
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Password</CardTitle>
          <CardDescription>Update your account password</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label
              htmlFor="current-password"
              className="block text-sm font-medium text-gray-700"
            >
              Current Password
            </label>
            <input
              id="current-password"
              type="password"
              className="mt-1 block w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label
              htmlFor="new-password"
              className="block text-sm font-medium text-gray-700"
            >
              New Password
            </label>
            <input
              id="new-password"
              type="password"
              className="mt-1 block w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div className="pt-2">
            <Button>Update Password</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Two-Factor Authentication</CardTitle>
          <CardDescription>
            Add an extra layer of security to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Two-factor authentication is currently{" "}
                <span className="font-medium text-gray-900">disabled</span>.
              </p>
            </div>
            <Button variant="outline">Enable 2FA</Button>
          </div>
        </CardContent>
      </Card>
    </>
  );
}
