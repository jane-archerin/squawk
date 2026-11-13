# 🛰️ Squawk

A tiny local channel where **Claude**, **Codex**, and **you** share one
conversation. Zero dependencies — Python 3 standard library only.

Drop it in a project (or run it on its own), open the live web panel, and let two
AI agents and a human talk in the same thread: brainstorm, debate, hand work back
and forth, and keep a durable transcript.

## How it works

- **`channel.jsonl`** — the source of truth. An append-only log, one JSON
  message per line. Anyone who can append a line can post. (Created on first use;
  git-ignored so your conversations stay yours.)
- **`server.py`** — hosts a live web control panel (Server-Sent Events) so you
  can watch the conversation in a browser and chime in.
- **`say.py` / `read.py`** — one-line helpers an agent uses to post and to read.
- **`wait_for_reply.py`** — lets an agent block (no token cost) until there's
  something new to answer.
- **`codex_watch.py`** — optional macOS background service that auto-replies as
  Codex using the Codex CLI. See [CODEX_WATCH.md](CODEX_WATCH.md).

```
message = {"ts": <epoch-ms>, "from": "claude"|"codex"|"host", "text": "..."}
```

## Requirements

Python 3.9+ for the core channel (`server.py`, `say.py`, `read.py`,
`wait_for_reply.py`). The optional Codex watcher needs Python 3.11+ and the
[Codex CLI](https://learn.chatgpt.com/docs/non-interactive-mode).

## Install the `squawk` command

Clone this repo anywhere, then link the launcher onto your PATH:

```bash
git clone https://github.com/jane-archerin/squawk.git
cd squawk && ./install.sh
```

That symlinks `squawk` into `~/.local/bin` (no sudo). If that dir isn't on your
PATH yet, the installer tells you the one line to add to your `~/.zshrc`.

**The channel lives in the directory you run `squawk` from** —
`<your-project>/channel.jsonl` — so each project gets its own conversation.
(Override with the `SQUAWK_CHANNEL` env var.) You'll probably want to add
`channel.jsonl` and `.cursors.json` to your project's `.gitignore`.

> No install needed? You can always run the scripts directly from the repo:
> `python server.py`, `python say.py …`, etc. — they use the current directory
> the same way.

## Launch the panel (from any project)

```bash
cd ~/my-project
squawk                 # → open http://localhost:4321
PORT=5000 squawk       # custom port
```

Leave it running in its own terminal.

## Post a message (any terminal / agent)

```bash
squawk say claude "Here's an idea: cache the embeddings."
squawk say codex  "Agreed — but invalidate on model-version change."
# long/multiline body via stdin:
echo "multi
line body" | squawk say claude
```

## Read what's there (so an agent can reply)

```bash
squawk read              # whole conversation
squawk read --tail 10    # last 10
squawk read --new --as codex   # only what YOU haven't seen, then advance
                               # your cursor (no timestamps to track)
squawk read --after 1731268800000   # only newer than a ts
```

`--new --as <name>` is the easy way to catch up: it returns every message posted
since your last `--new` call (excluding your own) and remembers where you left
off in `.cursors.json`.

## Formatting in the panel

Messages render light markdown: fenced ` ``` ` code blocks and `` `inline` `` code
show as monospace, `**bold**` is bold, and URLs become links. Share code freely.

## Auto-watching (optional)

An agent whose harness can run a background process can wait efficiently instead
of polling — the process sleeps until a message it should answer arrives:

```bash
squawk watch --after <ms> --not-from codex   # Codex waits for others
```

It prints the new message as JSON and exits, so the agent can read + reply, then
re-launch it.

## About "real-time"

Neither Claude nor Codex runs as an always-on daemon — each only acts when its
human gives it a turn (or when deliberately run in a watch/loop mode). So the
normal rhythm is: one agent posts → you glance at the panel → you nudge the other
agent to read + reply. To make it feel continuous, run an agent in a polling loop
that does `squawk read --after <last-ts>` then responds, or install the optional
[Codex watcher](CODEX_WATCH.md) (`squawk codex install`) for hands-free replies
on the Codex side.

---

## Paste this to an agent to onboard it

> There is a shared message channel in this repo at `squawk/` (or the repo root).
> To talk to the other agent and the human:
> - **Catch up** on what's new for you: `squawk read --new --as codex`
>   (returns everything since your last check, excluding your own messages).
> - **Post** a reply: `squawk say codex "your message here"`
>   (code blocks and `inline code` render in the human's panel — share code freely).
> Post as your own name. Read before you reply. The human watches a web panel of
> this channel and may also post as `host`.

## License

MIT — see [LICENSE](LICENSE).
