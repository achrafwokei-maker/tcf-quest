import { useEffect, useState } from "react";
import { Download, LogOut } from "lucide-react";
import { Button, Panel } from "./ui";
import { signOut, type Me } from "../lib/account";

/** Online only: download my data, sign out. Hidden in the local app. */
export function AccountPanel() {
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => { fetch("/api/beta/me").then((r) => r.json()).then(setMe).catch(() => setMe(null)); }, []);
  if (!me?.beta || !me.tester) return null;
  return (
    <Panel>
      <h2 className="text-xl">Account</h2>
      <p className="mb-3 text-sm text-ink-soft">Your progress is saved privately online. Download a copy any time (a JSON file you can keep).</p>
      <div className="flex flex-wrap gap-3">
        <a href="/api/account/export" download className="inline-flex"><Button variant="secondary"><Download aria-hidden className="size-4" /> Download my data</Button></a>
        <Button variant="secondary" onClick={() => void signOut(me.firebase)}><LogOut aria-hidden className="size-4" /> Sign out</Button>
      </div>
    </Panel>
  );
}
