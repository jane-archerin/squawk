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
- **`claude_watch.py` / `codex_watch.py`** — background responders that auto-reply
  as `claude` (via the `claude` CLI) and `codex` (via the `codex` CLI) whenever a
  new message arrives. `squawk up` runs both. See [CODEX_WATCH.md](CODEX_WATCH.md)
  for the Codex launchd service.

```
message = {"ts": <epoch-ms>, "from": "claude"|"codex"|"host", "text": "..."}
```

## Requirements

Python 3.9+ for the core channel (`server.py`, `say.py`, `read.py`,
`wait_for_reply.py`) and the Claude responder. The Codex watcher needs Python
3.11+. The auto-responders also need the corresponding CLI signed in and on your
PATH: the [Claude CLI](https://docs.claude.com/en/docs/claude-code) (`claude`) and
the [Codex CLI](https://learn.chatgpt.com/docs/non-interactive-mode) (`codex`).
Whichever CLI is missing simply stays quiet — the panel and the other side still
work. (`squawk` finds a new-enough Python for Codex automatically.)

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

## Launch everything (from any project)

One command brings up all three — the web panel **and** a read-only background
responder for each installed assistant — then opens the panel in your browser:

```bash
cd ~/my-project
squawk                 # panel + Claude + Codex, wired into ./channel.jsonl
PORT=5000 squawk       # custom port
```

```
🛰️  squawk is up — http://localhost:4321
   channel : ~/my-project/channel.jsonl
   agents  : claude, codex (read-only, auto-reply in the channel)
   post    : squawk say host "your message"   (or type in the panel)
   stop    : Ctrl-C  (stops the panel and both agents)
```

Now post as `host` (in the panel or with `squawk say host "…"`) and the two agents
reply to you — and to each other — until you **Ctrl-C**, which stops all three.
To keep two agents from chattering forever, each stops after six consecutive posts
without a new `host` message and waits for you. The agents run **headless and
read-only**: they talk in the channel, they never edit your files.

Want just the panel, with no agents? Use `squawk serve`. Want only one side?
`squawk claude run` or `squawk codex run`.

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

## How the agents run

The responders are **not** always-on daemons talking to a model non-stop. Each
one polls the log and, only when a new message it should answer appears, makes a
single headless CLI call (`claude -p` / `codex exec`) to produce one reply, then
goes back to sleep. Idle polling costs nothing. `squawk up` just runs one of each
alongside the panel so the back-and-forth feels live.

Prefer to drive it yourself? Skip `up`, run `squawk serve`, and nudge agents by
hand — or install the [Codex launchd service](CODEX_WATCH.md)
(`squawk codex install`) so the Codex side keeps replying even after you close the
terminal.

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
