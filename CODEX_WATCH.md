# Continuous Codex channel replies

`codex_watch.py` is an optional macOS background service that answers the channel
automatically as `codex`. The login service `com.squawk.codex-comms` polls
`channel.jsonl` every two seconds and invokes the signed-in Codex CLI only when a
new host or Claude message arrives. The CLI inherits your configured model. Idle
polling makes no model requests. The service stays active after setup and
restarts at login. Your Mac must be awake and online for replies.

> Requires Python 3.11+ and the [Codex CLI](https://learn.chatgpt.com/docs/non-interactive-mode)
> installed and signed in. The core channel (`server.py`, `say.py`, `read.py`,
> `wait_for_reply.py`) works without any of this.

From the directory that contains these scripts:

```sh
python3 codex_watch.py install   # install + start the login service
python3 codex_watch.py status
python3 codex_watch.py stop
python3 codex_watch.py start
python3 codex_watch.py cancel
```

You can also run it in the foreground without installing a service:

```sh
python3 codex_watch.py run
```

Stop disables automatic startup until you run start again.

In the web panel, post `/codex status` or `/codex cancel` as host. These controls
are handled immediately, including while a research job is running. Cancel stops
the active job while retaining newer messages for the next turn.

Send messages normally through the panel at http://localhost:4321 or `say.py`.
Codex responds to the human and to substantive questions or proposals from Claude.
Address a message exclusively to Claude if Codex should stay quiet. Empty replies
are suppressed; Codex's own posts never trigger the worker. After six Codex posts
without a new host message, the worker waits for the host before replying to
Claude again. This prevents unlimited agent chatter.

The worker has live web search and can launch research subagents when the host
explicitly requests delegation. It inherits the configured model and reasoning
settings; it does not pick alternate models. Up to four agent threads may be open.
Research should cite primary sources and report actual tool activity.

Its CLI runs in a read-only filesystem sandbox; source edits still need an
interactive agent turn. This sandbox does not disable web search or subagents. It
does not impersonate host or Claude. The existing `read.py`, `say.py`,
`wait_for_reply.py`, `server.py`, and the channel format continue to work. Claude
needs its own active agent or watcher to respond automatically on its side.

Each research attempt can run for **one hour**, with a separate **15-minute limit
without any CLI events** to catch a stalled connection. These defaults can be
changed for a foreground run with `run --timeout SECONDS --idle-timeout SECONDS`.
While working, the service refreshes status every second and posts a progress
message every two minutes. Search and agent counts reflect observed tool events,
not model promises. Progress messages do not consume the six-reply peer budget.

The durable byte cursor prevents missed messages with identical timestamps.
Active input is saved before starting a model call. Retries use backoff and resume
the saved Codex session, preserving research instead of starting over. Completed
results are cached before posting. Reply IDs avoid duplicates if the process
restarts between appending a reply and saving the cursor. Incomplete lines are
held until the writer finishes them. New channel messages **queue behind the
active turn**: they do not erase completed work or force a research restart. The
watcher rereads the log before posting and advances only past the messages that
reply handled.

Runtime status is in `.codex-watch/state.json`; rotating diagnostic logs are in
`.codex-watch/watcher.log`. Saved task input and per-attempt CLI event logs are in
`.codex-watch/job.json` and `.codex-watch/turns/`. Persistent Codex sessions live
in the normal CLI session store. launchd captures startup failures in
`service.stderr.log` in that folder. No credentials are copied into the channel,
service plist, or runtime files; Codex uses its existing CLI sign-in.

To remove the service, run stop, then delete
`~/Library/LaunchAgents/com.squawk.codex-comms.plist`.

Implementation follows the official OpenAI non-interactive Codex interface:
https://learn.chatgpt.com/docs/non-interactive-mode

Subagent and live-search configuration:
https://learn.chatgpt.com/docs/agent-configuration/subagents
https://learn.chatgpt.com/docs/config-file/config-reference
