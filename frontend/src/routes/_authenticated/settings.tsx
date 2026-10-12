import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Moon, Bell, KeyRound, LogOut, Check, Loader2, Globe } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError, type UserSettings } from "@/lib/api";
import { toast } from "sonner";

export const Route = createFileRoute("/_authenticated/settings")({
  head: () => ({
    meta: [{ title: "Settings — TradeVision AI" }],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const [settings, setSettings] = useState<UserSettings>({
    theme: "dark",
    default_exchange: "NSE",
    email_alerts: false,
  });
  const [loading, setLoading] = useState(true);
  const [savingTheme, setSavingTheme] = useState(false);
  const [savingAlerts, setSavingAlerts] = useState(false);

  // Change Password state
  const [pwdOpen, setPwdOpen] = useState(false);
  const [currentPwd, setCurrentPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [pwdLoading, setPwdLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await api.auth.getSettings();
        setSettings(data);
      } catch {
        // Defaults are fine if getSettings fails
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleToggleTheme = async (checked: boolean) => {
    const newTheme = checked ? "dark" : "light";
    setSavingTheme(true);
    try {
      await api.auth.updateSettings({ theme: newTheme });
      setSettings((prev) => ({ ...prev, theme: newTheme }));
      toast.success(`Theme set to ${newTheme} mode`);
    } catch {
      toast.error("Failed to update theme preference");
    } finally {
      setSavingTheme(false);
    }
  };

  const handleToggleAlerts = async (checked: boolean) => {
    setSavingAlerts(true);
    try {
      await api.auth.updateSettings({ email_alerts: checked });
      setSettings((prev) => ({ ...prev, email_alerts: checked }));
      toast.success(checked ? "Signal notifications enabled" : "Signal notifications disabled");
    } catch {
      toast.error("Failed to update notification settings");
    } finally {
      setSavingAlerts(false);
    }
  };

  const handleExchangeChange = async (exchange: string) => {
    try {
      await api.auth.updateSettings({ default_exchange: exchange });
      setSettings((prev) => ({ ...prev, default_exchange: exchange }));
      toast.success(`Default exchange updated to ${exchange}`);
    } catch {
      toast.error("Failed to update default exchange");
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPwd) {
      toast.error("Current password is required");
      return;
    }
    if (newPwd.length < 6) {
      toast.error("New password must be at least 6 characters");
      return;
    }
    if (newPwd !== confirmPwd) {
      toast.error("New passwords do not match");
      return;
    }

    setPwdLoading(true);
    try {
      const res = await api.auth.changePassword(currentPwd, newPwd);
      toast.success(res.message || "Password updated successfully");
      setPwdOpen(false);
      setCurrentPwd("");
      setNewPwd("");
      setConfirmPwd("");
    } catch (err) {
      toast.error("Could not change password", {
        description: err instanceof ApiError ? err.message : "Request failed",
      });
    } finally {
      setPwdLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Preferences"
        title="Settings"
        description="Configure your TradeVision experience and account preferences."
      />

      <div className="space-y-4">
        {/* Appearance */}
        <Section title="Appearance">
          <Row
            icon={Moon}
            title="Dark mode"
            description="Use dark interface for reduced glare and optimal chart viewing."
          >
            <Switch
              checked={settings.theme === "dark"}
              onCheckedChange={handleToggleTheme}
              disabled={loading || savingTheme}
              aria-label="Toggle dark mode"
            />
          </Row>
        </Section>

        {/* Notifications */}
        <Section title="Notifications">
          <Row
            icon={Bell}
            title="Signal alerts"
            description="Email notifications for high-confidence market signals."
          >
            <Switch
              checked={settings.email_alerts}
              onCheckedChange={handleToggleAlerts}
              disabled={loading || savingAlerts}
              aria-label="Toggle signal alerts"
            />
          </Row>
        </Section>

        {/* Market Preferences */}
        <Section title="Market Preferences">
          <Row
            icon={Globe}
            title="Default exchange"
            description="Default exchange used for resolving ambiguous tickers."
          >
            <div className="flex items-center gap-1.5">
              {["NSE", "BSE", "NASDAQ", "NYSE"].map((ex) => (
                <button
                  key={ex}
                  type="button"
                  onClick={() => handleExchangeChange(ex)}
                  className={`rounded-md px-2.5 py-1 font-mono text-xs transition-colors ${
                    (settings.default_exchange || "NSE") === ex
                      ? "bg-primary text-primary-foreground font-semibold"
                      : "border border-border bg-panel/40 text-muted-foreground hover:bg-panel hover:text-foreground"
                  }`}
                >
                  {ex}
                </button>
              ))}
            </div>
          </Row>
        </Section>

        {/* Security */}
        <Section title="Security">
          <Row
            icon={KeyRound}
            title="Change password"
            description="Update the password used to sign in to your account."
          >
            <Dialog open={pwdOpen} onOpenChange={setPwdOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm">
                  Change password
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <form onSubmit={handleChangePassword}>
                  <DialogHeader>
                    <DialogTitle>Change Password</DialogTitle>
                    <DialogDescription>
                      Enter your current password and choose a new secure password.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="space-y-3.5 py-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="current-pwd">Current Password</Label>
                      <Input
                        id="current-pwd"
                        type="password"
                        value={currentPwd}
                        onChange={(e) => setCurrentPwd(e.target.value)}
                        placeholder="••••••••"
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="new-pwd">New Password (min 6 chars)</Label>
                      <Input
                        id="new-pwd"
                        type="password"
                        value={newPwd}
                        onChange={(e) => setNewPwd(e.target.value)}
                        placeholder="••••••••"
                        required
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="confirm-pwd">Confirm New Password</Label>
                      <Input
                        id="confirm-pwd"
                        type="password"
                        value={confirmPwd}
                        onChange={(e) => setConfirmPwd(e.target.value)}
                        placeholder="••••••••"
                        required
                      />
                    </div>
                  </div>

                  <DialogFooter className="gap-2 sm:gap-0">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setPwdOpen(false)}
                      disabled={pwdLoading}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={pwdLoading}>
                      {pwdLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Updating…
                        </>
                      ) : (
                        <>
                          <Check className="mr-1.5 h-4 w-4" />
                          Update password
                        </>
                      )}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </Row>
        </Section>

        {/* Account */}
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
