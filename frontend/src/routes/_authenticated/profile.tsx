import { createFileRoute, Link } from "@tanstack/react-router";
import { Mail, Hash, Calendar, ShieldCheck, History, Star, Settings as SettingsIcon } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { useAuth } from "@/lib/auth-context";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_authenticated/profile")({
  head: () => ({
    meta: [{ title: "Profile — TradeVision AI" }],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user, status } = useAuth();

  const formattedDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "Active Member";

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Your verified TradeVision user credentials and workspace overview."
      />

      <div className="glass-panel rounded-xl p-6">
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-primary/40 bg-primary/10 text-xl font-bold text-primary shadow-inner">
            {user?.email ? user.email[0]?.toUpperCase() : "·"}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                Account Status
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-500">
                <ShieldCheck className="h-3 w-3" /> Verified
              </span>
            </div>
            {status === "loading" ? (
              <Skeleton className="mt-1 h-6 w-48" />
            ) : (
              <p className="mt-0.5 text-lg font-semibold text-foreground">{user?.email}</p>
            )}
          </div>
        </div>

        <div className="grid gap-3">
          <Field icon={Mail} label="Email Address" value={user?.email ?? "—"} mono />
          <Field icon={Hash} label="User Identifier (UUID)" value={String(user?.id ?? "—")} mono />
          <Field icon={Calendar} label="Member Since" value={formattedDate} />
        </div>
      </div>

      {/* Quick Access Card */}
      <div className="mt-6 glass-panel rounded-xl p-6">
        <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Quick Navigation
        </h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Jump to your trading archives and preferences.
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <Button asChild variant="outline" className="justify-start gap-2 h-auto py-3">
            <Link to="/history">
              <History className="h-4 w-4 text-primary" />
              <div className="text-left">
                <div className="text-xs font-semibold">History</div>
                <div className="text-[10px] text-muted-foreground">Past analyses</div>
              </div>
            </Link>
          </Button>

          <Button asChild variant="outline" className="justify-start gap-2 h-auto py-3">
            <Link to="/watchlist">
              <Star className="h-4 w-4 text-amber-500" />
              <div className="text-left">
                <div className="text-xs font-semibold">Watchlist</div>
                <div className="text-[10px] text-muted-foreground">Tracked stocks</div>
              </div>
            </Link>
          </Button>

          <Button asChild variant="outline" className="justify-start gap-2 h-auto py-3">
            <Link to="/settings">
              <SettingsIcon className="h-4 w-4 text-primary" />
              <div className="text-left">
                <div className="text-xs font-semibold">Settings</div>
                <div className="text-[10px] text-muted-foreground">Security &amp; theme</div>
              </div>
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({
  icon: Icon,
  label,
  value,
  mono,
}: {
  icon: typeof Mail;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-background/40 px-4 py-3">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-muted-foreground" strokeWidth={1.5} />
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <span className={`text-sm text-foreground ${mono ? "font-mono" : ""}`}>{value}</span>
    </div>
  );
}
