import { createFileRoute } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { Star, Plus, X } from "lucide-react";
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
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow="Tracking"
        title="Watchlist"
        description="Symbols you want TradeVision to keep an eye on. Kept locally for now — cloud sync coming soon."
      />

      <form
        onSubmit={add}
        className="glass-panel mb-6 flex items-center gap-2 rounded-xl p-3"
      >
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Add symbol (e.g. BTCUSDT, AAPL, ES1!)"
          className="border-0 bg-transparent font-mono uppercase tracking-wider shadow-none focus-visible:ring-0"
          autoCapitalize="characters"
        />
        <Button type="submit" size="sm" disabled={!symbol.trim()}>
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
        <ul className="glass-panel divide-y divide-border overflow-hidden rounded-xl">
          {symbols.map((s) => (
            <li
              key={s}
              className="flex items-center justify-between px-5 py-3 transition-colors hover:bg-primary/5"
            >
              <div className="flex items-center gap-3">
                <Star className="h-4 w-4 text-primary" fill="currentColor" strokeWidth={1.5} />
                <span className="font-mono text-sm font-medium tracking-wider text-foreground">
                  {s}
                </span>
              </div>
              <button
                onClick={() => remove(s)}
                className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                aria-label={`Remove ${s}`}
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
