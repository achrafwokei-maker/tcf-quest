import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Button, CompassMark, Loading, Panel } from "./ui";

interface Me { beta: boolean; tester: string | null }

/** Online beta only: asks for the personal invite code once, then remembers it (secure cookie). Locally it renders the app directly. */
export function InviteGate({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [waking, setWaking] = useState(false);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    const slow = setTimeout(() => alive && setWaking(true), 4000);
    const ask = (tries: number): Promise<void> =>
      fetch("/api/beta/me").then((r) => r.json() as Promise<Me>).then((m) => { if (alive) setMe(m); })
        .catch(() => (tries > 0 && alive ? new Promise((ok) => setTimeout(ok, 3000)).then(() => ask(tries - 1)) : undefined))
        .then(() => { if (alive && tries === 0) setMe((m) => m ?? { beta: false, tester: null }); });
    void ask(20).finally(() => clearTimeout(slow));
    return () => { alive = false; clearTimeout(slow); };
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await fetch("/api/beta/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code }) });
      const body = await r.json();
      if (!r.ok) throw new Error(body.detail ?? "Something went wrong.");
      setMe(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  if (!me) return <div className="mx-auto max-w-xl px-6"><Loading label={waking ? "Waking the server up, about a minute…" : undefined} /></div>;
  if (!me.beta || me.tester) return <>{children}</>;

  return (
    <div className="mx-auto max-w-md px-5 py-16">
      <Panel className="space-y-4 text-center">
        <CompassMark className="mx-auto size-12" />
        <h1 className="title-poster text-4xl">TCF Quest · beta</h1>
        <p className="font-semibold text-ink-soft">Enter the personal invite code you were given. Your progress is saved privately under it.</p>
        <form onSubmit={submit} className="space-y-3">
          <label className="block text-left">
            <span className="text-sm font-extrabold">Invite code</span>
            <input value={code} onChange={(e) => setCode(e.target.value)} autoComplete="off" autoCapitalize="none" spellCheck={false}
              className="mt-1 w-full rounded-[14px] border-2 border-line bg-surface-2 px-4 py-3 text-lg font-bold" />
          </label>
          {error && <p role="alert" className="text-sm font-bold text-danger">{error}</p>}
          <Button type="submit" disabled={busy || code.trim().length < 4} className="w-full">Start</Button>
        </form>
        <p className="text-xs font-semibold text-ink-faint">Training app for the TCF Canada. Scores are estimates, never official results.</p>
      </Panel>
    </div>
  );
}
