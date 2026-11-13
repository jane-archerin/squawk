#!/usr/bin/env python3
"""
Post one message to the agent comms channel.

Usage:
    python say.py <from> <message...>
    echo "long message" | python say.py <from>   # read body from stdin

Examples:
    python say.py claude "I think we should cache the embeddings."
    python say.py codex  "Agreed, but invalidate on model version change."

It appends a line to channel.jsonl. The running web panel (server.py)
picks it up live. The server does NOT need to be running to post — the log is
the source of truth — but you won't see it in the browser until the server runs.
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


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python say.py <from> <message...>   (or pipe body via stdin)")
    sender = sys.argv[1].strip().lower()[:32]
    if len(sys.argv) > 2:
        text = " ".join(sys.argv[2:])
    else:
        text = sys.stdin.read()
    text = text.strip()
    if not text:
        sys.exit("refusing to post empty message")
    msg = {"ts": int(time.time() * 1000), "from": sender, "text": text}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    print(f"posted as {sender}: {text[:60]}{'…' if len(text) > 60 else ''}")


if __name__ == "__main__":
    main()
