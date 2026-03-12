"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <main
        className={cn(
          "transition-all duration-200",
          sidebarCollapsed ? "ml-16" : "ml-60",
        )}
      >
        {children}
      </main>
    </div>
  );
}
