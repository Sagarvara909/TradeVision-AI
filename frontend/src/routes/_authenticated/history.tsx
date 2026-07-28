import { createFileRoute, Link } from "@tanstack/react-router";
import { History as HistoryIcon, Upload } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_authenticated/history")({
  head: () => ({
    meta: [{ title: "History — TradeVision AI" }],
  }),
  component: HistoryPage,
});

function HistoryPage() {
  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        eyebrow="Archive"
        title="Analysis history"
        description="Every analysis you run is saved here for review, comparison, and export."
      />

      <div className="glass-panel overflow-hidden rounded-xl">
        <div className="grid grid-cols-[1.5fr_1fr_1fr_0.8fr_0.5fr] gap-4 border-b border-border px-5 py-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <span>Symbol</span>
          <span>Signal</span>
          <span>Confidence</span>
          <span>Timestamp</span>
          <span className="text-right">—</span>
        </div>
        <div className="p-6">
          <EmptyState
            icon={HistoryIcon}
            title="No analyses yet"
            description="Once you upload and analyze a chart, it will appear here with its signal, confidence, and full reasoning report."
            action={
              <Button asChild>
                <Link to="/upload">
                  <Upload className="mr-1.5 h-4 w-4" />
                  Run your first analysis
                </Link>
              </Button>
            }
          />
        </div>
      </div>
    </div>
  );
}
