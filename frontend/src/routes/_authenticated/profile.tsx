import { createFileRoute } from "@tanstack/react-router";
import { Mail, Hash, Shield } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { useAuth } from "@/lib/auth-context";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/_authenticated/profile")({
  head: () => ({
    meta: [{ title: "Profile — TradeVision AI" }],
  }),
  component: ProfilePage,
});

function ProfilePage() {
  const { user, status } = useAuth();

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Account"
        title="Profile"
        description="Your account details as returned by the backend."
      />

      <div className="glass-panel rounded-xl p-6">
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full border border-primary/40 bg-primary/10 text-lg font-semibold text-primary">
            {user?.email ? user.email[0]?.toUpperCase() : "·"}
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
              Signed in as
            </p>
            {status === "loading" ? (
              <Skeleton className="mt-1 h-5 w-48" />
            ) : (
              <p className="text-base font-medium text-foreground">{user?.email}</p>
            )}
          </div>
        </div>

        <div className="grid gap-3">
          <Field icon={Mail} label="Email" value={user?.email ?? "—"} mono />
          <Field icon={Hash} label="User ID" value={String(user?.id ?? "—")} mono />
          <Field icon={Shield} label="Plan" value="Early access" />
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Profile settings — display name, avatar, notification preferences — coming soon.
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
      <span className={`text-sm text-foreground ${mono ? "font-mono" : ""}`}>
        {value}
      </span>
    </div>
  );
}
