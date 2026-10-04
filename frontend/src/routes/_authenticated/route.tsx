import { createFileRoute, Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_authenticated")({
  ssr: false,
  component: AuthenticatedLayout,
});

function AuthenticatedLayout() {
  const { status, user, logout } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const pageTitle =
    pathname === "/dashboard"
      ? "Dashboard"
      : pathname === "/upload"
        ? "Chart analysis"
        : pathname === "/history"
          ? "Analysis history"
          : pathname === "/watchlist"
            ? "Watchlist"
            : pathname === "/profile"
              ? "Profile"
              : pathname === "/settings"
                ? "Settings"
                : "TradeVision AI";

  useEffect(() => {
    if (status === "unauthenticated") {
      navigate({ to: "/login", replace: true });
    }
  }, [status, navigate]);

  if (status !== "authenticated") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          <span className="font-mono text-xs uppercase tracking-widest">Verifying session</span>
        </div>
      </div>
    );
  }

  return (
    <SidebarProvider defaultOpen={false}>
      <div className="flex min-h-screen w-full bg-background">
        <AppSidebar />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 flex h-[68px] items-center justify-between border-b border-border bg-white/90 px-4 backdrop-blur-md sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <SidebarTrigger
                aria-label="Toggle navigation"
                className="text-muted-foreground hover:bg-accent hover:text-primary"
              />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-foreground">{pageTitle}</p>
                <p className="hidden text-xs text-muted-foreground sm:block">
                  Your workspace overview
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 sm:gap-4">
              <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 sm:flex">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                <span className="text-xs font-medium text-emerald-800">Session active</span>
              </div>
              <div className="flex min-w-0 items-center gap-2.5 border-l border-border pl-3 sm:pl-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                  {user?.email?.[0]?.toUpperCase() ?? "U"}
                </div>
                <span className="hidden max-w-44 truncate text-sm font-medium text-foreground md:inline">
                  {user?.email}
                </span>
              </div>
            </div>
          </header>
          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            <Outlet />
          </main>
          <footer className="flex items-center justify-between gap-3 border-t border-border/80 px-4 py-4 text-xs text-muted-foreground sm:px-6 lg:px-8">
            <span className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-primary" /> Explainable market intelligence
            </span>
            <span className="hidden sm:inline">For informational purposes only</span>
          </footer>
        </div>
      </div>
    </SidebarProvider>
  );
}
