import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { AuthLayout } from "@/components/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-context";
import { api, ApiError } from "@/lib/api";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Create your account — TradeVision AI" },
      {
        name: "description",
        content: "Create your TradeVision AI account to start analyzing charts.",
      },
      { property: "og:title", content: "Create your account — TradeVision AI" },
      {
        property: "og:description",
        content: "Create your TradeVision AI account to start analyzing charts.",
      },
    ],
  }),
  component: RegisterPage,
});

function validatePassword(pw: string): string | null {
  if (pw.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Za-z]/.test(pw) || !/[0-9]/.test(pw))
    return "Password must contain both letters and numbers.";
  return null;
}

function RegisterPage() {
  const { status } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (status === "authenticated") {
      navigate({ to: "/dashboard", replace: true });
    }
  }, [status, navigate]);

  useEffect(() => {
    if (!success) return;
    const t = setTimeout(() => navigate({ to: "/login", replace: true }), 1600);
    return () => clearTimeout(t);
  }, [success, navigate]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!/\S+@\S+\.\S+/.test(email)) {
      setError("Please enter a valid email address.");
      return;
    }
    const pwErr = validatePassword(password);
    if (pwErr) {
      setError(pwErr);
      return;
    }

    setSubmitting(true);
    try {
      await api.auth.register(email.trim(), password);
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 0) setError("Can't reach the server. Check your connection.");
        else if (err.status === 409 || err.status === 400)
          setError(err.message || "That email is already registered.");
        else setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <AuthLayout
        title="Account created"
        subtitle="Redirecting you to sign in…"
        footer={
          <Link to="/login" className="font-medium text-primary hover:underline">
            Go to sign in now
          </Link>
        }
      >
        <div className="flex items-start gap-3 rounded-md border border-success/40 bg-success/10 px-3 py-3 text-sm text-foreground">
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
          <span>
            Your account is ready. Sign in with your email and password to continue.
          </span>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Free while in early access. No credit card."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={submitting}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={submitting}
            required
          />
          <p className="font-mono text-[11px] text-muted-foreground">
            Min 8 chars · letters + numbers required
          </p>
        </div>

        {error ? (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Creating account…
            </>
          ) : (
            "Create account"
          )}
        </Button>
      </form>
    </AuthLayout>
  );
}
