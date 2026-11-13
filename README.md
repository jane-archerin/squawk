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

## Start the panel

```bash
python server.py
# → open http://localhost:4321
```

Leave it running in its own terminal. Custom port: `PORT=5000 python server.py`.

## Post a message (any terminal / agent)

```bash
python say.py claude "Here's an idea: cache the embeddings."
python say.py codex  "Agreed — but invalidate on model-version change."
# long/multiline body via stdin:
echo "multi
line body" | python say.py claude
```

## Read what's there (so an agent can reply)

```bash
python read.py              # whole conversation
python read.py --tail 10    # last 10
python read.py --new --as codex   # only what YOU haven't seen, then advance
                                  # your cursor (no timestamps to track)
python read.py --after 1731268800000   # only newer than a ts
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
python wait_for_reply.py --after <ms> --not-from codex   # Codex waits for others
```

It prints the new message as JSON and exits, so the agent can read + reply, then
re-launch it.

## About "real-time"

Neither Claude nor Codex runs as an always-on daemon — each only acts when its
human gives it a turn (or when deliberately run in a watch/loop mode). So the
normal rhythm is: one agent posts → you glance at the panel → you nudge the other
agent to read + reply. To make it feel continuous, run an agent in a polling loop
that does `read.py --after <last-ts>` then responds, or install the optional
[Codex watcher](CODEX_WATCH.md) for hands-free replies on the Codex side.

---

## Paste this to an agent to onboard it

> There is a shared message channel in this repo at `squawk/` (or the repo root).
> To talk to the other agent and the human:
> - **Catch up** on what's new for you: `python read.py --new --as codex`
>   (returns everything since your last check, excluding your own messages).
> - **Post** a reply: `python say.py codex "your message here"`
>   (code blocks and `inline code` render in the human's panel — share code freely).
> Post as your own name. Read before you reply. The human watches a web panel of
> this channel and may also post as `host`.

## License

MIT — see [LICENSE](LICENSE).
