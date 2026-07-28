import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Moon, Bell, KeyRound, LogOut } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/lib/auth-context";

export const Route = createFileRoute("/_authenticated/settings")({
  head: () => ({
    meta: [{ title: "Settings — TradeVision AI" }],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Preferences"
        title="Settings"
        description="Configure your TradeVision experience."
      />

      <div className="space-y-4">
        <Section title="Appearance">
          <Row
            icon={Moon}
            title="Dark mode"
            description="TradeVision is dark by default. A light theme is planned."
          >
            <Switch checked disabled aria-label="Dark mode (always on)" />
          </Row>
        </Section>

        <Section title="Notifications">
          <Row
            icon={Bell}
            title="Signal alerts"
            description="Email notifications for new signals on watchlist symbols."
          >
            <Switch disabled aria-label="Signal alerts (coming soon)" />
          </Row>
        </Section>

        <Section title="Security">
          <Row
            icon={KeyRound}
            title="Change password"
            description="Update the password used to sign in."
          >
            <Button variant="outline" size="sm" disabled>
              Coming soon
            </Button>
          </Row>
        </Section>

        <Section title="Account">
          <Row
            icon={LogOut}
            title="Sign out"
            description="End your current session on this device."
          >
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                logout();
                navigate({ to: "/login", replace: true });
              }}
            >
              Sign out
            </Button>
          </Row>
        </Section>
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="glass-panel overflow-hidden rounded-xl">
      <div className="border-b border-border px-5 py-3">
        <p className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
          {title}
        </p>
      </div>
      <div className="divide-y divide-border">{children}</div>
    </div>
  );
}

function Row({
  icon: Icon,
  title,
  description,
  children,
}: {
  icon: typeof Moon;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 px-5 py-4">
      <div className="flex min-w-0 items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-border bg-background/60 text-muted-foreground">
          <Icon className="h-4 w-4" strokeWidth={1.5} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}
