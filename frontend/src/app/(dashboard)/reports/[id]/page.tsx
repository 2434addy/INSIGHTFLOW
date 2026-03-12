import type { Metadata } from "next";
import { ReportContent } from "./report-content";

export const metadata: Metadata = {
  title: "Report",
};

export default function ReportPage({ params }: { params: { id: string } }) {
  return <ReportContent reportId={params.id} />;
}
