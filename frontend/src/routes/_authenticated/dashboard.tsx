import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Upload,
  TrendingUp,
  Clock,
  LineChart,
  ScanLine,
  BrainCircuit,
  FileText,
  ArrowUpRight,
} from "lucide-react";
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
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow="Your workspace"
        title="Welcome to TradeVision"
        description="Turn a chart into clear, explainable market analysis."
        actions={
          <Button asChild>
            <Link to="/upload">
              <Upload className="mr-1.5 h-4 w-4" />
              Analyze a chart
            </Link>
          </Button>
        }
      />

      <div className="mb-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <FeatureCard
          step="01"
          title="Upload a chart"
          description="Start with a PNG, JPEG, or WebP chart image."
          icon={ScanLine}
          href="/upload"
        />
        <FeatureCard
          step="02"
          title="Review indicators"
          description="Inspect the technical and risk analysis returned for the detected symbol."
          icon={TrendingUp}
          href="/upload"
        />
        <FeatureCard
          step="03"
          title="Understand the report"
          description="Generate an AI explanation grounded in the available analysis."
          icon={BrainCircuit}
          href="/upload"
        />
      </div>

      <section className="overflow-hidden rounded-2xl border border-border bg-white shadow-[0_4px_24px_rgb(15_23_42_/_4%)]">
        <div className="flex flex-col gap-4 border-b border-border px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <FileText className="h-4 w-4" />
              </div>
              <h2 className="text-sm font-semibold text-foreground">Recent analyses</h2>
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              Reports you create will be available in your history.
            </p>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link to="/history">
              View history <ArrowUpRight className="ml-1.5 h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
        <div className="p-4 sm:p-6">
          <EmptyState
            icon={Clock}
            title="No analyses yet"
            description="Upload a chart to begin. Once you create a report, your analysis history will appear here."
            action={
              <Button asChild>
                <Link to="/upload">
                  <Upload className="mr-1.5 h-4 w-4" />
                  Start an analysis
                </Link>
              </Button>
            }
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({
  step,
  title,
  description,
  icon: Icon,
  href,
}: {
  step: string;
  title: string;
  description: string;
  icon: typeof LineChart;
  href: "/upload";
}) {
  return (
    <Link
      to={href}
      className="group rounded-2xl border border-border bg-white p-5 shadow-[0_2px_10px_rgb(15_23_42_/_3%)] transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-[0_10px_28px_rgb(109_93_251_/_9%)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    >
      <div className="flex items-start justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-white">
          <Icon className="h-5 w-5" strokeWidth={1.8} />
        </div>
        <span className="font-mono text-xs font-medium text-muted-foreground/70">{step}</span>
      </div>
      <h2 className="mt-5 text-sm font-semibold text-foreground">{title}</h2>
      <p className="mt-1.5 text-sm leading-6 text-muted-foreground">{description}</p>
    </Link>
  );
}
