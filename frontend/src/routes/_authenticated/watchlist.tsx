import { createFileRoute } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { Star, Plus, X, Bookmark } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/_authenticated/watchlist")({
  head: () => ({
    meta: [{ title: "Watchlist — TradeVision AI" }],
  }),
  component: WatchlistPage,
});

function WatchlistPage() {
  const [symbol, setSymbol] = useState("");
  const [symbols, setSymbols] = useState<string[]>([]);

  const add = (e: FormEvent) => {
    e.preventDefault();
    const s = symbol.trim().toUpperCase();
    if (!s) return;
    if (symbols.includes(s)) {
      setSymbol("");
      return;
    }
    setSymbols([...symbols, s]);
    setSymbol("");
  };

  const remove = (s: string) => setSymbols(symbols.filter((x) => x !== s));

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        eyebrow="Tracking"
        title="Watchlist"
        description="Keep symbols you want to revisit in one place."
      />

      <form
        onSubmit={add}
        className="mb-6 flex flex-col gap-3 rounded-2xl border border-border bg-white p-4 shadow-[0_2px_10px_rgb(15_23_42_/_3%)] sm:flex-row"
      >
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Add symbol (e.g. BTCUSDT, AAPL, ES1!)"
          className="h-11 border-border bg-background/60 font-mono uppercase tracking-wider shadow-none sm:flex-1"
          autoCapitalize="characters"
          aria-label="Stock symbol to add"
        />
        <Button type="submit" className="h-11 px-5" disabled={!symbol.trim()}>
          <Plus className="mr-1 h-4 w-4" />
          Add
        </Button>
      </form>

      {symbols.length === 0 ? (
        <EmptyState
          icon={Star}
          title="Your watchlist is empty"
          description="Add a symbol above to start tracking it. TradeVision will surface signals for watched symbols first."
        />
      ) : (
        <section className="overflow-hidden rounded-2xl border border-border bg-white shadow-[0_4px_24px_rgb(15_23_42_/_4%)]">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] border-b border-border bg-slate-50/70 px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            <span>Symbol</span>
            <span>Actions</span>
          </div>
          <ul className="divide-y divide-border">
            {symbols.map((s) => (
              <li
                key={s}
                className="grid grid-cols-[minmax(0,1fr)_auto] items-center px-5 py-4 transition-colors hover:bg-primary/[0.025]"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Star className="h-4 w-4" fill="currentColor" strokeWidth={1.5} />
                  </div>
                  <div className="min-w-0">
                    <span className="block truncate font-mono text-sm font-semibold tracking-wide text-foreground">
                      {s}
                    </span>
                    <span className="mt-0.5 flex items-center gap-1 text-xs text-muted-foreground">
                      <Bookmark className="h-3 w-3" /> Saved to your watchlist
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => remove(s)}
                    className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-red-50 hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    aria-label={`Remove ${s} from watchlist`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
