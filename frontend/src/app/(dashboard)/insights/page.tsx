import type { Metadata } from "next";
import { InsightsContent } from "./insights-content";

export const metadata: Metadata = {
  title: "Insights",
};

export default function InsightsPage() {
  return <InsightsContent />;
}
