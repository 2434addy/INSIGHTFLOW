import type { Metadata } from "next";
import { CampaignsContent } from "./campaigns-content";

export const metadata: Metadata = {
  title: "Campaign Performance",
};

export default function CampaignsPage() {
  return <CampaignsContent />;
}
