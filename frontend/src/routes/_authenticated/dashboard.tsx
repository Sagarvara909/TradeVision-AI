import { createFileRoute, Link } from "@tanstack/react-router";
import { Upload, TrendingUp, Clock, LineChart } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_authenticated/dashboard")({
  head: () => ({
    meta: [{ title: "Dashboard — TradeVision AI" }],
  }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Your recent analyses and signals will appear here."
        actions={
          <Button asChild>
            <Link to="/upload">
              <Upload className="mr-1.5 h-4 w-4" />
              New analysis
            </Link>
          </Button>
        }
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <StatCard label="Analyses" value="0" icon={LineChart} />
        <StatCard label="Watchlist" value="0" icon={TrendingUp} />
        <StatCard label="Last signal" value="—" icon={Clock} />
      </div>

      <EmptyState
        icon={Upload}
        title="Upload your first chart to get started"
        description="Drop a TradingView screenshot on the Upload page. TradeVision will read the chart, run its indicators, and explain what it sees — step by step."
        action={
          <Button asChild>
            <Link to="/upload">
              <Upload className="mr-1.5 h-4 w-4" />
              Upload a chart
            </Link>
          </Button>
        }
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof LineChart;
}) {
  return (
    <div className="rounded-xl border border-border bg-panel/40 p-4">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          {label}
        </p>
        <Icon className="h-4 w-4 text-muted-foreground" strokeWidth={1.5} />
      </div>
      <p className="mt-3 font-mono text-2xl font-semibold tracking-tight text-foreground">
        {value}
      </p>
    </div>
  );
}
