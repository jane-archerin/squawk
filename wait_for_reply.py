#!/usr/bin/env python3
"""
Block until a NEW message appears on the channel from someone other than a
given sender, then print it as JSON and exit. Used to let an agent "watch"
the channel efficiently: the process sleeps in the shell (no token cost) and
only exits when there's something to respond to.

Usage:
    python wait_for_reply.py --after <epoch_ms> [--not-from claude]
                                   [--host-gate <n>] [--timeout <sec>]

--host-gate <n> prevents an infinite agent-to-agent loop: once you (the
--not-from sender) have posted <n> messages with no host message in between,
the watcher ignores other agents' messages and only wakes on a host message.
This mirrors the cap the other side runs. 0 (default) disables the gate.

Exit/print:
    prints one JSON object (the new message) and exits 0 when a match arrives
    prints {"timeout": true} and exits 0 if --timeout elapses with nothing
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.abspath(
    os.environ.get("SQUAWK_CHANNEL")
    or os.path.join(os.getcwd(), "channel.jsonl")
)


def arg(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    after = float(arg("--after", "0"))
    not_from = (arg("--not-from", "claude") or "claude").lower()
    only_from = (arg("--from", "") or "").lower()
    host_gate = int(arg("--host-gate", "0") or 0)
    timeout = arg("--timeout")
    deadline = time.time() + float(timeout) if timeout else None

    while True:
        try:
            with open(LOG, encoding="utf-8") as f:
                msgs = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msgs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            # How many of MY posts since the last host message? (for the gate)
            last_host = max((m["ts"] for m in msgs if m.get("from", "").lower() == "host"), default=0)
            my_since_host = sum(1 for m in msgs if m.get("from", "").lower() == not_from and m["ts"] > last_host)
            gated = host_gate and my_since_host >= host_gate
            for m in msgs:
                frm = m.get("from", "").lower()
                if m.get("ts", 0) <= after or frm == not_from:
                    continue
                # Positive filter: if --from is set, only wake on that sender.
                if only_from and frm != only_from:
                    continue
                # Skip automated progress heartbeats (not real content).
                text = m.get("text", "")
                if any(s in text for s in (
                    "still working on the current request",
                    "Observed parent activity",
                    "New channel messages are queued",
                )):
                    continue
                # When gated, only a host message may wake us.
                if gated and frm != "host":
                    continue
                print(json.dumps(m, ensure_ascii=False))
                return
        except FileNotFoundError:
            pass
        if deadline and time.time() > deadline:
            print(json.dumps({"timeout": True}))
            return
        time.sleep(1)


if __name__ == "__main__":
    main()
