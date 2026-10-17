import { Check, CircleAlert, Mic, MessageCircle, Volume2 } from "lucide-react";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Link } from "react-router-dom";
import { Badge, ErrorNote, IconTile, Loading, Panel } from "../components/ui";

export function Tutor() {
  const [state, reload] = useAsync(api.health);
  const [vs] = useAsync(() => fetch("/api/voices").then((r) => r.json() as Promise<{ worker_running: boolean }>));
  const voices = vs.status === "ready" && vs.data.worker_running;
  if (state.status === "loading") return <Loading label="Checking the local AI…" />;
  if (state.status === "error") return <ErrorNote error={state.error} onRetry={reload} />;
  const ai = state.data.ai;
  const ready = ai.running && ai.model_installed;

  return (
    <div className="space-y-8 px-5 pt-6 sm:px-10 sm:pt-10">
      <header>
        <p className="eyebrow">Mon Professeur IA</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Your French tutor</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          The tutor runs entirely on this Mac. Your words and recordings never leave it.
        </p>
      </header>

      <Panel>
        <h2 className="text-xl">Local AI status</h2>
        <ul className="mt-4 space-y-3">
          <StatusRow ok={ai.running} label="Ollama (the local AI engine)" detail={ai.running ? `Running, version ${ai.version}` : "Not running. Open the Ollama app."} />
          <StatusRow ok={ai.model_installed} label={`Language model: ${ai.model}`} detail={ai.model_installed ? "Installed" : "Not installed yet"} />
          <StatusRow ok={voices} label="French voices and speech recognition" detail={voices ? "Running on your Mac" : "Not running. Restart the app with scripts/dev.sh."} />
        </ul>
        {ready && <p className="mt-5 text-success">The AI is ready.</p>}
      </Panel>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { icon: MessageCircle, color: "var(--violet)", title: "Writing feedback", detail: "Write a TCF task, get corrections and a revised version.", to: "/ecrit" },
          { icon: Mic, color: "var(--pink)", title: "Spoken role-play", detail: "Phone the club, the landlord, M. Delaunay…", to: "/oral" },
          { icon: Volume2, color: "var(--blue)", title: "Examiner mode", detail: "Speaking tasks T1–T3 at the official timing.", to: "/oral" },
        ].map(({ icon, color, title, detail, to }) => (
          <Link key={title} to={to} className="card p-4 transition-transform hover:-translate-y-1 sm:p-5">
            <div className="flex items-center justify-between">
              <IconTile icon={icon} color={color} size="sm" />
              <Badge tone="success">Open</Badge>
            </div>
            <p className="mt-3 font-semibold">{title}</p>
            <p className="text-sm text-ink-faint">{detail}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

function StatusRow({ ok, label, detail, pending }: { ok: boolean; label: string; detail: string; pending?: boolean }) {
  return (
    <li className="flex items-start gap-3">
      {ok ? (
        <Check aria-hidden className="mt-0.5 size-5 text-success" />
      ) : pending ? (
        <span aria-hidden className="mt-1.5 size-3 rounded-full border-2 border-line" />
      ) : (
        <CircleAlert aria-hidden className="mt-0.5 size-5 text-warning" />
      )}
      <div className="flex-1">
        <p className="font-semibold">{label}</p>
        <p className="text-sm text-ink-faint">{detail}</p>
      </div>
      {ok ? <Badge tone="success">Ready</Badge> : pending ? <Badge>Planned</Badge> : <Badge tone="warning">Action needed</Badge>}
    </li>
  );
}
