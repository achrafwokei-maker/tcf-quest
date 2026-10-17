# Start here: continue TCF Quest in Claude Code

You have 3 files:

- **CLAUDE.md**: Claude reads this automatically. It holds the vision, the "no code yet" rule, the stack, the art direction and the 12 open decisions.
- **docs/blueprint.md**: the full blueprint.
- **START-HERE.md**: this guide.

## Where the project lives

The project folder is **~/tcf-quest** (your home folder → tcf-quest). It is not in Documents, because macOS blocks Claude from reading the Documents folder on this Mac.

```
tcf-quest/
  CLAUDE.md
  START-HERE.md
  docs/
    blueprint.md
```

## Opening it

- Desktop app: open Claude, choose the Code tab, then pick the tcf-quest folder.
- Terminal: open a terminal in the folder and type `claude`.

## Running the app

```
scripts/dev.sh
```

Then open http://localhost:5173. Progress is saved in `data/` on this Mac. Where the build stands: `docs/PROGRESS.md`.

## Good to know

- Development was approved on 2026-10-16 (free local plan). Rules for Claude are in CLAUDE.md.
- Decisions are logged in docs/DECISIONS.md, so every future session remembers them.
- Git is set up: every milestone is saved and can be undone.
