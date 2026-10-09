import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { Star, Plus, X, RefreshCw, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { api, ApiError, type WatchlistItem } from "@/lib/api";

export const Route = createFileRoute("/_authenticated/watchlist")({
  head: () => ({
    meta: [{ title: "Watchlist — TradeVision AI" }],
  }),
  component: WatchlistPage,
});

function changeColor(change: number | null) {
  if (change === null) return "text-muted-foreground";
  return change >= 0 ? "text-emerald-500" : "text-red-500";
}

function WatchlistPage() {
  const [symbol, setSymbol] = useState("");
  const [exchange, setExchange] = useState("");
  const [items, setItems] = useState<WatchlistItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [adding, setAdding] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const data = await api.watchlist.list();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load your watchlist");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const add = async (e: FormEvent) => {
    e.preventDefault();
    const s = symbol.trim().toUpperCase();
    if (!s || adding) return;
    setAdding(true);
    try {
      const created = await api.watchlist.add(s, exchange.trim().toUpperCase() || undefined);
      setItems((prev) => [created, ...(prev ?? [])]);
      setSymbol("");
      setExchange("");
      toast.success(`${created.symbol} added`);
    } catch (err) {
      // e.g. 409 "already on your watchlist"
      toast.error("Could not add symbol", {
        description: err instanceof ApiError ? err.message : "Something went wrong",
      });
    } finally {
      setAdding(false);
    }
  };

  const remove = async (item: WatchlistItem) => {
    setRemovingId(item.id);
    try {
      await api.watchlist.remove(item.id);
      setItems((prev) => (prev ?? []).filter((x) => x.id !== item.id));
    } catch (err) {
      toast.error("Could not remove symbol", {
        description: err instanceof ApiError ? err.message : "Something went wrong",
      });
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow="Tracking"
        title="Watchlist"
        description="Symbols you want to keep an eye on, with live prices. Add the exchange (NSE, BSE, NASDAQ…) so Indian tickers resolve correctly."
      />

      <form
        onSubmit={add}
        className="glass-panel mb-6 flex items-center gap-2 rounded-xl p-3"
      >
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Symbol (e.g. TCS, AAPL)"
          className="flex-1 border-0 bg-transparent font-mono uppercase tracking-wider shadow-none focus-visible:ring-0"
          autoCapitalize="characters"
        />
        <Input
          value={exchange}
          onChange={(e) => setExchange(e.target.value)}
          placeholder="Exchange (NSE)"
          className="w-36 border-0 bg-transparent font-mono uppercase tracking-wider shadow-none focus-visible:ring-0"
          autoCapitalize="characters"
        />
        <Button type="submit" size="sm" disabled={!symbol.trim() || adding}>
          {adding ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Plus className="mr-1 h-4 w-4" />
          )}
          Add
        </Button>
      </form>

      {loading ? (
        <div className="glass-panel space-y-3 rounded-xl p-5">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      ) : !items || items.length === 0 ? (
        <EmptyState
          icon={Star}
          title="Your watchlist is empty"
          description="Add a symbol above, or use the Watchlist button on any analysis, to start tracking it with live prices."
        />
      ) : (
        <>
          <div className="mb-2 flex justify-end">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => load(true)}
              disabled={refreshing}
              className="text-xs text-muted-foreground"
            >
              <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
              Refresh prices
            </Button>
          </div>
          <ul className="glass-panel divide-y divide-border overflow-hidden rounded-xl">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-primary/5"
              >
                <div className="flex items-center gap-3">
                  <Star className="h-4 w-4 text-primary" fill="currentColor" strokeWidth={1.5} />
                  <div>
                    <span className="font-mono text-sm font-medium tracking-wider text-foreground">
                      {item.symbol}
                    </span>
                    {item.exchange ? (
                      <span className="ml-2 rounded border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                        {item.exchange}
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="flex items-center gap-5">
                  {item.price !== null ? (
                    <div className="text-right">
                      <p className="font-mono text-sm text-foreground">{item.price.toFixed(2)}</p>
                      <p className={`font-mono text-[11px] ${changeColor(item.percent_change)}`}>
                        {item.percent_change !== null
                          ? `${item.percent_change >= 0 ? "+" : ""}${item.percent_change.toFixed(2)}%`
                          : "—"}
                      </p>
                    </div>
                  ) : (
                    <p
                      className="max-w-[220px] truncate text-right text-[11px] text-muted-foreground"
                      title={item.quote_error ?? undefined}
                    >
                      {item.quote_error ?? "Price unavailable"}
                    </p>
                  )}
                  <button
                    onClick={() => remove(item)}
                    disabled={removingId === item.id}
                    className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive disabled:opacity-50"
                    aria-label={`Remove ${item.symbol}`}
                  >
                    {removingId === item.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <X className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}