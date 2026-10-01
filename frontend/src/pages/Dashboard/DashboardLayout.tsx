import React from "react";
import { Outlet } from "react-router-dom";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";

export const DashboardLayout: React.FC = () => {
  return (
    <SidebarProvider>
      <AppSidebar variant="inset" />
      <SidebarInset className="bg-card border border-border/70 shadow-xs">
        <SiteHeader />
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
};
