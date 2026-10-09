import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  History as HistoryIcon,
  Upload,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  Download,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError, type HistoryEntry, type Report } from "@/lib/api";

export const Route = createFileRoute("/_authenticated/history")({
  head: () => ({
    meta: [{ title: "History — TradeVision AI" }],
  }),
  component: HistoryPage,
});

function trendIcon(trend: string | null) {
  if (trend === "uptrend") return <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />;
  if (trend === "downtrend") return <TrendingDown className="h-3.5 w-3.5 text-red-500" />;
  return <Minus className="h-3.5 w-3.5 text-muted-foreground" />;
}

function riskColor(level: string) {
  if (level === "low") return "text-emerald-500";
  if (level === "high") return "text-red-500";
  return "text-amber-500";
}

function formatWhen(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detailCache, setDetailCache] = useState<Record<string, Report>>({});
  const [detailLoading, setDetailLoading] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.history.list();
        setEntries(data.entries);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not load history");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const [pdfLoadingId, setPdfLoadingId] = useState<string | null>(null);

  const downloadPdf = async (reportId: string, symbol: string) => {
    setPdfLoadingId(reportId);
    try {
      await api.reports.downloadPdf(reportId, symbol);
    } catch (err) {
      toast.error("PDF download failed", {
        description: err instanceof ApiError ? err.message : "Could not download the PDF",
      });
    } finally {
      setPdfLoadingId(null);
    }
  };

  const toggleExpand = async (reportId: string) => {
    if (expandedId === reportId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(reportId);
    setDetailError(null);
    if (detailCache[reportId]) return;

    setDetailLoading(reportId);
    try {
      const report = await api.reports.get(reportId);
      setDetailCache((prev) => ({ ...prev, [reportId]: report }));
    } catch (err) {
      setDetailError(err instanceof ApiError ? err.message : "Could not load this report");
    } finally {
      setDetailLoading(null);
    }
  };

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

        {loading ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : error ? (
          <div className="p-6">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        ) : !entries || entries.length === 0 ? (
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
        ) : (
          <div className="divide-y divide-border/60">
            {entries.map((entry) => {
              const isOpen = expandedId === entry.report_id;
              const detail = detailCache[entry.report_id];
              return (
                <div key={entry.report_id}>
                  <button
                    type="button"
                    onClick={() => toggleExpand(entry.report_id)}
                    className="grid w-full grid-cols-[1.5fr_1fr_1fr_0.8fr_0.5fr] items-center gap-4 px-5 py-3 text-left text-sm transition-colors hover:bg-panel/40"
                  >
                    <span className="font-mono text-foreground">{entry.symbol}</span>
                    <span className="flex items-center gap-1.5 capitalize text-muted-foreground">
                      {trendIcon(entry.trend)}
                      {entry.trend ?? "—"}
                    </span>
                    <span className="text-foreground">
                      {entry.confidence_score}/100{" "}
                      <span className={`text-xs capitalize ${riskColor(entry.risk_level)}`}>
                        ({entry.risk_level})
                      </span>
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">
                      {formatWhen(entry.last_viewed_at)}
                    </span>
                    <span className="flex justify-end">
                      <ChevronDown
                        className={`h-4 w-4 text-muted-foreground transition-transform ${isOpen ? "rotate-180" : ""}`}
                      />
                    </span>
                  </button>

                  {isOpen ? (
                    <div className="border-t border-border/40 bg-panel/20 px-5 py-4">
                      {detailLoading === entry.report_id ? (
                        <div className="space-y-2">
                          <Skeleton className="h-4 w-full" />
                          <Skeleton className="h-4 w-5/6" />
                          <Skeleton className="h-4 w-3/4" />
                        </div>
                      ) : detailError ? (
                        <div className="flex items-start gap-2 text-sm text-destructive">
                          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                          {detailError}
                        </div>
                      ) : detail ? (
                        <>
                          <ul className="mb-3 space-y-1 text-xs text-muted-foreground">
                            {detail.reasoning.map((line, i) => (
                              <li key={i} className="flex gap-2">
                                <span className="text-primary">·</span>
                                {line}
                              </li>
                            ))}
                          </ul>
                          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                            {detail.llm_report}
                          </p>
                          <div className="mt-3 flex justify-end">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => downloadPdf(entry.report_id, entry.symbol)}
                              disabled={pdfLoadingId === entry.report_id}
                            >
                              {pdfLoadingId === entry.report_id ? (
                                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                              ) : (
                                <Download className="mr-1.5 h-3.5 w-3.5" />
                              )}
                              Download PDF
                            </Button>
                          </div>
                        </>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}