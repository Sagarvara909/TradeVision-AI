import { Link } from "@tanstack/react-router";
import { Activity } from "lucide-react";
import type { ReactNode } from "react";

export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4 py-10">
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-30" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[400px] bg-[radial-gradient(ellipse_at_top,color-mix(in_oklab,var(--primary)_15%,transparent),transparent_60%)]" />

      <div className="relative z-10 w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md border border-primary/40 bg-primary/10 text-primary">
            <Activity className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight">TradeVision</span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              AI · v0.1
            </span>
          </div>
        </Link>

        <div className="glass-panel rounded-xl p-6 shadow-xl shadow-primary/5">
          <div className="mb-6">
            <h1 className="text-xl font-semibold tracking-tight text-foreground">
              {title}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          </div>
          {children}
        </div>

        <div className="mt-5 text-center text-sm text-muted-foreground">
          {footer}
        </div>
      </div>
    </div>
  );
}
