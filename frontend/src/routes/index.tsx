import { createFileRoute, Link } from "@tanstack/react-router";
import { Activity, ArrowRight, BarChart3, Brain, Eye, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "TradeVision AI — Explainable trading decision support" },
      {
        name: "description",
        content:
          "A decision-support tool for chart-driven traders. Understand why a signal fires — with transparent, explainable technical analysis.",
      },
      { property: "og:title", content: "TradeVision AI" },
      {
        property: "og:description",
        content:
          "Explainable AI for trading decisions. Not a bot. Not automation. Just clarity.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* Background grid */}
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-40" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[600px] bg-[radial-gradient(ellipse_at_top,color-mix(in_oklab,var(--primary)_18%,transparent),transparent_60%)]" />

      {/* Nav */}
      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-primary/40 bg-primary/10 text-primary">
            <Activity className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-semibold tracking-tight">TradeVision</span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              AI · v0.1
            </span>
          </div>
        </Link>
        <nav className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link to="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm">
            <Link to="/register">
              Get started <ArrowRight className="ml-1 h-3.5 w-3.5" />
            </Link>
          </Button>
        </nav>
      </header>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pt-16 pb-24 md:pt-24 md:pb-32">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-panel/60 px-3 py-1 backdrop-blur">
            <span className="h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_8px] shadow-primary/60" />
            <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              Decision support · Not a bot
            </span>
          </div>
          <h1 className="text-balance text-4xl font-semibold tracking-tight text-foreground md:text-6xl">
            Understand{" "}
            <span className="text-primary">why</span>{" "}
            a signal fires.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-pretty text-base text-muted-foreground md:text-lg">
            TradeVision AI reads your charts, applies transparent technical analysis, and
            explains its reasoning in plain language. You keep the trade. We give you the
            <span className="text-foreground"> "why"</span>.
          </p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link to="/register">
                Get started <ArrowRight className="ml-1.5 h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/login">I already have an account</Link>
            </Button>
          </div>

          <p className="mt-6 font-mono text-xs text-muted-foreground">
            No auto-execution. No get-rich-quick claims. Educational analysis only.
          </p>
        </div>

        {/* Terminal preview */}
        <div className="mx-auto mt-16 max-w-4xl">
          <div className="glass-panel overflow-hidden rounded-xl shadow-2xl shadow-primary/5">
            <div className="flex items-center gap-2 border-b border-border/60 bg-panel/60 px-4 py-2.5">
              <div className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-destructive/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-warning/60" />
                <span className="h-2.5 w-2.5 rounded-full bg-success/60" />
              </div>
              <span className="ml-2 font-mono text-[11px] text-muted-foreground">
                tradevision · signal · BTCUSDT · 4H
              </span>
            </div>
            <div className="grid gap-px bg-border/60 md:grid-cols-3">
              <TerminalStat label="Signal" value="LONG" tone="success" mono />
              <TerminalStat label="Confidence" value="72%" mono />
              <TerminalStat label="RR" value="1 : 2.4" mono />
            </div>
            <div className="space-y-3 border-t border-border/60 bg-background/40 p-5">
              <ReasoningLine
                tag="RSI"
                text="Oversold reversal on 4H (28.4 → 41.2) — momentum flip confirmed."
              />
              <ReasoningLine
                tag="EMA"
                text="Price reclaimed 200 EMA at 61,240 — prior resistance now support."
              />
              <ReasoningLine
                tag="Vol"
                text="Buying volume up 38% vs. 20-bar avg on the reclaim candle."
              />
            </div>
          </div>
        </div>
      </section>

      {/* What it is / isn't */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-24">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="glass-panel rounded-xl p-6">
            <p className="font-mono text-[11px] uppercase tracking-widest text-primary">
              What it is
            </p>
            <ul className="mt-4 space-y-3 text-sm text-foreground">
              <Bullet>Transparent, explainable technical analysis</Bullet>
              <Bullet>Chart-in, reasoning-out — you upload, we explain</Bullet>
              <Bullet>Every signal cites its indicators and thresholds</Bullet>
            </ul>
          </div>
          <div className="glass-panel rounded-xl p-6">
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              What it isn't
            </p>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <Bullet tone="muted">Not an automated trading bot</Bullet>
              <Bullet tone="muted">Not financial advice or a profit guarantee</Bullet>
              <Bullet tone="muted">Not a black box — no unexplained "buy" calls</Bullet>
            </ul>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <Feature
            icon={Eye}
            title="Explainable"
            text="Every conclusion cites the indicators, timeframes, and thresholds that produced it."
          />
          <Feature
            icon={Brain}
            title="Analytical"
            text="Multi-indicator confluence — RSI, EMA, MACD, volume — evaluated against classical rules."
          />
          <Feature
            icon={ShieldCheck}
            title="You stay in control"
            text="TradeVision informs the decision. The trade is always yours to place."
          />
        </div>
      </section>

      <footer className="relative z-10 border-t border-border/60 bg-background/60">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-6 py-6 text-xs text-muted-foreground md:flex-row">
          <p className="font-mono">© TradeVision AI · Educational tool only</p>
          <p>Not investment advice. Trade at your own risk.</p>
        </div>
      </footer>
    </div>
  );
}

function TerminalStat({
  label,
  value,
  tone,
  mono,
}: {
  label: string;
  value: string;
  tone?: "success";
  mono?: boolean;
}) {
  return (
    <div className="bg-panel/40 p-4">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
      <p
        className={`mt-1.5 text-2xl font-semibold ${mono ? "font-mono" : ""} ${
          tone === "success" ? "text-success" : "text-foreground"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function ReasoningLine({ tag, text }: { tag: string; text: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 rounded border border-primary/30 bg-primary/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-primary">
        {tag}
      </span>
      <p className="text-sm text-muted-foreground">
        <span className="text-foreground">{text.split(" — ")[0]}</span>
        {text.includes(" — ") ? ` — ${text.split(" — ")[1]}` : null}
      </p>
    </div>
  );
}

function Bullet({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: "muted";
}) {
  return (
    <li className="flex items-start gap-2.5">
      <span
        className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${
          tone === "muted" ? "bg-muted-foreground/50" : "bg-primary"
        }`}
      />
      <span>{children}</span>
    </li>
  );
}

function Feature({
  icon: Icon,
  title,
  text,
}: {
  icon: typeof BarChart3;
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-panel/40 p-5">
      <div className="flex h-9 w-9 items-center justify-center rounded-md border border-primary/30 bg-primary/10 text-primary">
        <Icon className="h-4 w-4" strokeWidth={1.75} />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-foreground">{title}</h3>
      <p className="mt-1.5 text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
