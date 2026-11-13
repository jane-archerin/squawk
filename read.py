#!/usr/bin/env python3
"""
Read messages from the agent comms channel (so an agent can see what was said).

Usage:
    python read.py                 # print the whole conversation
    python read.py --tail 10       # last 10 messages
    python read.py --after <ms>    # only messages with ts > <ms> (poll for new)
    python read.py --new --as codex  # only messages YOU (codex) haven't seen,
                                           # then advance your cursor. No ts to track.
    python read.py --json          # raw JSONL (for machine parsing)

The easiest way for an agent to catch up: `python read.py --new --as <you>`.
It returns everything posted since your last `--new` call (excluding your own
messages) and remembers where you left off, in .cursors.json.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.abspath(
    os.environ.get("SQUAWK_CHANNEL")
    or os.path.join(os.getcwd(), "channel.jsonl")
)
CURSORS = os.path.join(os.path.dirname(LOG), ".cursors.json")


def load_cursors():
    try:
        with open(CURSORS, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cursor(name, ts):
    cur = load_cursors()
    cur[name] = ts
    tmp = CURSORS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cur, f)
    os.replace(tmp, CURSORS)


def load():
    msgs = []
    try:
        with open(LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        msgs.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return msgs


def fmt(m):
    import datetime
    t = datetime.datetime.fromtimestamp(m["ts"] / 1000).strftime("%H:%M:%S")
    return f"[{t}] {m['from']}: {m['text']}"


def main():
    args = sys.argv[1:]
    msgs = load()
    if "--new" in args:
        me = args[args.index("--as") + 1].strip().lower() if "--as" in args else None
        if not me:
            sys.exit("--new requires --as <your-name>, e.g. --new --as codex")
        since = load_cursors().get(me, 0)
        msgs = [m for m in msgs if m["ts"] > since and m.get("from", "").lower() != me]
        if msgs:
            save_cursor(me, max(m["ts"] for m in msgs))
    if "--after" in args:
        ts = float(args[args.index("--after") + 1])
        msgs = [m for m in msgs if m["ts"] > ts]
    if "--tail" in args:
        n = int(args[args.index("--tail") + 1])
        msgs = msgs[-n:]
    if "--json" in args:
        for m in msgs:
            print(json.dumps(m, ensure_ascii=False))
    else:
        if not msgs:
            print("(no messages)")
        for m in msgs:
            print(fmt(m))


if __name__ == "__main__":
    main()
