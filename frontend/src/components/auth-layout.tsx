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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[radial-gradient(ellipse_at_15%_0%,#eeeafe_0%,transparent_38%),#f7f8fc] px-4 py-10">
      <div className="relative z-10 w-full max-w-md">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/20">
            <Activity className="h-[18px] w-[18px]" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight">TradeVision</span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              MARKET INTELLIGENCE
            </span>
          </div>
        </Link>

        <div className="rounded-2xl border border-border bg-white p-6 shadow-[0_16px_50px_rgb(15_23_42_/_8%)] sm:p-8">
          <div className="mb-6">
            <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          </div>
          {children}
        </div>

        <div className="mt-5 text-center text-sm text-muted-foreground">{footer}</div>
      </div>
    </div>
  );
}
