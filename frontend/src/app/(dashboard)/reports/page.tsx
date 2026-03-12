import type { Metadata } from "next";
import { ReportsListContent } from "./reports-list-content";

export const metadata: Metadata = {
  title: "Reports",
};

export default function ReportsPage() {
  return <ReportsListContent />;
}
