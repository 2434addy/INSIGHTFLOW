"use client";

import { PageHeader } from "@/components/common/page-header";
import { EmptyState } from "@/components/common/empty-state";
import { Topbar } from "@/components/layout/topbar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ReportStatus } from "@/types/api";
import { FileText, Plus } from "lucide-react";
import Link from "next/link";

interface ReportListItem {
  id: string;
  title: string;
  status: ReportStatus;
  date_range: string;
  platforms: string[];
  created_at: string;
  insights_count: number;
}

const DEMO_REPORTS: ReportListItem[] = [
  {
    id: "rpt_001",
    title: "February 2026 Performance Report",
    status: "completed",
    date_range: "Feb 1 - Feb 28, 2026",
    platforms: ["Meta Ads", "Google Ads"],
    created_at: "Mar 1, 2026",
    insights_count: 5,
  },
  {
    id: "rpt_002",
    title: "January 2026 Performance Report",
    status: "completed",
    date_range: "Jan 1 - Jan 31, 2026",
    platforms: ["Meta Ads", "Google Ads", "Shopify"],
    created_at: "Feb 1, 2026",
    insights_count: 7,
  },
  {
    id: "rpt_003",
    title: "Q4 2025 Quarterly Review",
    status: "completed",
    date_range: "Oct 1 - Dec 31, 2025",
    platforms: ["Meta Ads", "Google Ads"],
    created_at: "Jan 5, 2026",
    insights_count: 12,
  },
  {
    id: "rpt_004",
    title: "March 2026 Weekly Snapshot",
    status: "generating",
    date_range: "Mar 1 - Mar 7, 2026",
    platforms: ["Meta Ads"],
    created_at: "Mar 8, 2026",
    insights_count: 0,
  },
];

const STATUS_VARIANT = {
  completed: "success",
  generating: "default",
  failed: "danger",
} as const;

export function ReportsListContent() {
  return (
    <>
      <Topbar title="Reports" />
      <div className="space-y-6 p-6">
        <PageHeader
          title="Reports"
          description="AI-generated performance reports"
          actions={
            <Button>
              <Plus className="h-4 w-4" />
              Generate Report
            </Button>
          }
        />

        {DEMO_REPORTS.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-12 w-12" />}
            title="No reports yet"
            description="Generate your first AI-powered performance report to get started."
            actionLabel="Generate Report"
            onAction={() => {}}
          />
        ) : (
          <div className="space-y-3">
            {DEMO_REPORTS.map((report) => (
              <Link key={report.id} href={`/reports/${report.id}`}>
                <Card className="cursor-pointer transition-shadow hover:shadow-md">
                  <CardContent className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                      <div className="rounded-lg bg-blue-50 p-2.5">
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900">
                          {report.title}
                        </h3>
                        <div className="mt-1 flex items-center gap-3 text-sm text-gray-500">
                          <span>{report.date_range}</span>
                          <span>|</span>
                          <span>{report.platforms.join(", ")}</span>
                          {report.insights_count > 0 && (
                            <>
                              <span>|</span>
                              <span>{report.insights_count} insights</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-500">
                        {report.created_at}
                      </span>
                      <Badge variant={STATUS_VARIANT[report.status]}>
                        {report.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
