import { useState, type FormEvent } from "react";
import { Button, CompassMark, Panel } from "./ui";
import { confirmVerified, NeedsVerification, resetPassword, signInWithEmail, signInWithGoogle,
  type FirebaseConfig, type Me } from "../lib/account";

/** Online sign-in: Google in one tap, or email + password (with email confirmation and password reset). */
export function AccountSignIn({ config, onSignedIn }: { config: FirebaseConfig; onSignedIn: (m: Me) => void }) {
  const [mode, setMode] = useState<"in" | "create">("in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [busy, setBusy] = useState(false);

  async function run(fn: () => Promise<Me | void>) {
    setBusy(true); setError(null); setNote(null);
    try {
      const me = await fn();
      if (me) onSignedIn(me);
    } catch (e) {
      if (e instanceof NeedsVerification) setVerifying(true);
      setError(e instanceof Error ? e.message : "Sign-in failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const submit = (e: FormEvent) => { e.preventDefault(); void run(() => signInWithEmail(config, email, password, mode === "create")); };
  const field = "mt-1 w-full rounded-[14px] border-2 border-line bg-surface-2 px-4 py-3 text-lg font-bold";

  return (
    <div className="mx-auto max-w-md px-5 py-12">
      <Panel className="space-y-4">
        <div className="text-center">
          <CompassMark className="mx-auto size-12" />
          <h1 className="title-poster mt-2 text-4xl">TCF Quest</h1>
          <p className="font-semibold text-ink-soft">{mode === "create" ? "Create your free account. Your progress is saved privately." : "Sign in to continue your progress."}</p>
        </div>

        <Button className="w-full" variant="secondary" disabled={busy} onClick={() => run(() => signInWithGoogle(config))}>
          <GoogleMark /> Continue with Google
        </Button>
        <p className="text-center text-xs font-extrabold uppercase tracking-wider text-ink-faint">or with email</p>

        {verifying ? (
          <div className="space-y-3">
            <p role="status" className="rounded-[14px] bg-surface-2 p-3 text-sm font-semibold">{error}</p>
            <Button className="w-full" disabled={busy} onClick={() => run(() => confirmVerified(config))}>I've confirmed my email</Button>
            <button type="button" className="w-full text-sm font-bold text-ink-soft underline" onClick={() => { setVerifying(false); setError(null); }}>Back</button>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <label className="block">
              <span className="text-sm font-extrabold">Email</span>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" className={field} />
            </label>
            <label className="block">
              <span className="text-sm font-extrabold">Password</span>
              <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "create" ? "new-password" : "current-password"} className={field} />
            </label>
            {error && <p role="alert" className="text-sm font-bold text-danger">{error}</p>}
            {note && <p role="status" className="text-sm font-bold text-success">{note}</p>}
            <Button type="submit" className="w-full" disabled={busy}>{mode === "create" ? "Create account" : "Sign in"}</Button>
            <div className="flex flex-wrap justify-between gap-2 text-sm font-bold text-ink-soft">
              <button type="button" className="underline" onClick={() => { setMode(mode === "in" ? "create" : "in"); setError(null); }}>
                {mode === "in" ? "New here? Create an account" : "I already have an account"}
              </button>
              {mode === "in" && (
                <button type="button" className="underline" disabled={busy}
                  onClick={() => email ? run(async () => { await resetPassword(config, email); setNote("Password reset email sent."); }) : setError("Type your email first.")}>
                  Forgot password?
                </button>
              )}
            </div>
          </form>
        )}
        <p className="text-center text-xs font-semibold text-ink-faint">Training app for the TCF Canada. Scores are estimates, never official results.</p>
      </Panel>
    </div>
  );
}

function GoogleMark() {
  return (
    <svg aria-hidden viewBox="0 0 24 24" className="size-5">
      <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5a5.6 5.6 0 0 1-2.4 3.6v3h3.9c2.3-2.1 3.5-5.2 3.5-8.8z" />
      <path fill="#34A853" d="M12 24c3.2 0 6-1.1 8-2.9l-3.9-3c-1.1.7-2.5 1.2-4.1 1.2-3.1 0-5.8-2.1-6.7-5H1.3v3.1A12 12 0 0 0 12 24z" />
      <path fill="#FBBC05" d="M5.3 14.3a7.2 7.2 0 0 1 0-4.6V6.6H1.3a12 12 0 0 0 0 10.8l4-3.1z" />
      <path fill="#EA4335" d="M12 4.8c1.8 0 3.3.6 4.6 1.8l3.4-3.4A12 12 0 0 0 1.3 6.6l4 3.1c.9-2.9 3.6-4.9 6.7-4.9z" />
    </svg>
  );
}
