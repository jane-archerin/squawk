#!/usr/bin/env python3
"""
Agent comms control panel.

A tiny zero-dependency server (Python stdlib only) that hosts a live web
control panel where Claude, Codex, and you (the host) share one conversation.

Source of truth is an append-only log: channel.jsonl (one JSON object per line).
Anyone who can append a line to that file can post. The browser panel shows it
live via Server-Sent Events.

Run:   python server.py            # serves http://localhost:4321
       PORT=5000 python server.py  # custom port

Post from an agent/terminal:
       python say.py claude "here's an idea..."
       python say.py codex  "I'd do it differently because..."
"""
import json
import os
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.abspath(
    os.environ.get("SQUAWK_CHANNEL")
    or os.path.join(os.getcwd(), "channel.jsonl")
)
PORT = int(os.environ.get("PORT", "4321"))

_write_lock = threading.Lock()


def append_message(sender: str, text: str) -> dict:
    """Append one message to the log atomically. Returns the stored object."""
    sender = (sender or "unknown").strip().lower()[:32]
    msg = {"ts": int(time.time() * 1000), "from": sender, "text": text}
    line = json.dumps(msg, ensure_ascii=False) + "\n"
    with _write_lock:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    return msg


def ensure_log():
    if not os.path.exists(LOG):
        open(LOG, "a", encoding="utf-8").close()


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Squawk</title>
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --border: #2a3139; --text: #e6edf3;
    --muted: #8b949e; --host: #d29922; --claude: #a371f7; --codex: #2f81f7;
    --input-bg: #0d1117;
  }
  @media (prefers-color-scheme: light) {
    :root:not([data-theme="dark"]) {
      --bg:#f6f8fa; --panel:#fff; --border:#d0d7de; --text:#1f2328;
      --muted:#636c76; --host:#9a6700; --claude:#8250df; --codex:#0969da;
      --input-bg:#fff;
    }
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    background: var(--bg); color: var(--text);
    font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    display: flex; flex-direction: column; height: 100vh;
  }
  header {
    padding: 12px 16px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 12px; background: var(--panel);
    flex: 0 0 auto;
  }
  header h1 { font-size: 15px; margin: 0; font-weight: 600; letter-spacing: .2px; }
  #status { font-size: 12px; color: var(--muted); display: flex; align-items: center; gap: 6px; margin-left: auto; }
  #dot { width: 8px; height: 8px; border-radius: 50%; background: #d29922; }
  #dot.live { background: #3fb950; }
  #dot.dead { background: #f85149; }
  #log { flex: 1 1 auto; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 760px; width: fit-content; }
  .msg .meta { font-size: 12px; color: var(--muted); margin: 0 0 3px 2px; }
  .msg .meta b { font-weight: 600; }
  .bubble {
    padding: 9px 13px; border-radius: 12px; white-space: pre-wrap; word-break: break-word;
    border: 1px solid var(--border); background: var(--panel);
  }
  .from-claude .meta b { color: var(--claude); }
  .from-codex  .meta b { color: var(--codex); }
  .from-host   .meta b { color: var(--host); }
  .from-claude .bubble { border-left: 3px solid var(--claude); }
  .from-codex  .bubble { border-left: 3px solid var(--codex); }
  .from-host   { align-self: flex-end; }
  .from-host   .bubble { border-left: none; border-right: 3px solid var(--host); }
  .from-host   .meta { text-align: right; margin: 0 2px 3px 0; }
  .empty { color: var(--muted); text-align: center; margin: auto; font-size: 14px; }
  .bubble pre { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 9px 11px; overflow-x: auto; margin: 6px 0; }
  .bubble pre code { display: block; white-space: pre; background: none; border: none; padding: 0; }
  .bubble code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }
  .bubble :not(pre) > code { background: var(--bg); border: 1px solid var(--border); border-radius: 4px; padding: 1px 5px; }
  .bubble a { color: var(--codex); }
  form {
    flex: 0 0 auto; display: flex; gap: 8px; padding: 12px 16px;
    border-top: 1px solid var(--border); background: var(--panel);
  }
  select, textarea, button {
    font: inherit; color: var(--text); background: var(--input-bg);
    border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px;
  }
  textarea { flex: 1; resize: none; min-height: 40px; max-height: 160px; }
  select { flex: 0 0 auto; }
  button { cursor: pointer; background: var(--codex); color: #fff; border-color: transparent; font-weight: 600; padding: 8px 16px; }
  button:disabled { opacity: .5; cursor: default; }
</style>
</head>
<body>
  <header>
    <h1>🛰️ Squawk</h1>
    <div id="status"><span id="dot"></span><span id="statustext">connecting…</span></div>
  </header>
  <div id="log"><div class="empty">No messages yet. Say hello below, or have an agent post.</div></div>
  <form id="composer">
    <select id="from" title="Post as">
      <option value="host" selected>you (host)</option>
      <option value="claude">claude</option>
      <option value="codex">codex</option>
    </select>
    <textarea id="text" placeholder="Type a message…  (Enter to send, Shift+Enter for newline)" autofocus></textarea>
    <button type="submit" id="send">Send</button>
  </form>

<script>
  const logEl = document.getElementById('log');
  const dot = document.getElementById('dot');
  const statusText = document.getElementById('statustext');
  const seen = new Set();
  let emptied = false;

  function fmtTime(ts) {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
  }
  // Minimal, XSS-safe formatting: fenced code, inline code, bold, links.
  function formatMessage(text) {
    const blocks = [];
    let t = String(text).replace(/```[a-zA-Z0-9]*\n?([\s\S]*?)```/g, (_, code) => {
      blocks.push(code.replace(/\n$/, '')); return '\u0000' + (blocks.length - 1) + '\u0000';
    });
    t = escapeHtml(t);
    t = t.replace(/`([^`\n]+)`/g, (_, c) => '<code>' + c + '</code>');
    t = t.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    t = t.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    t = t.replace(/\u0000(\d+)\u0000/g, (_, i) => '<pre><code>' + escapeHtml(blocks[+i]) + '</code></pre>');
    return t;
  }

  function render(i, m) {
    if (seen.has(i)) return;
    seen.add(i);
    if (!emptied) { logEl.innerHTML = ''; emptied = true; }
    const who = (m.from || 'unknown');
    const wrap = document.createElement('div');
    wrap.className = 'msg from-' + (['claude','codex','host'].includes(who) ? who : 'other');
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.innerHTML = '<b>' + who + '</b> · ' + fmtTime(m.ts);
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = formatMessage(m.text);
    wrap.appendChild(meta); wrap.appendChild(bubble);
    logEl.appendChild(wrap);
    const nearBottom = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 150;
    if (nearBottom) logEl.scrollTop = logEl.scrollHeight;
  }

  function connect() {
    const es = new EventSource('/api/stream');
    es.onopen = () => { dot.className = 'live'; statusText.textContent = 'live'; };
    es.onmessage = (e) => {
      try { const o = JSON.parse(e.data); render(o.i, o); } catch (_) {}
    };
    es.onerror = () => {
      dot.className = 'dead'; statusText.textContent = 'reconnecting…';
      // EventSource auto-reconnects; dedup via `seen` handles replayed history.
    };
  }
  connect();

  const form = document.getElementById('composer');
  const textEl = document.getElementById('text');
  const fromEl = document.getElementById('from');

  async function send() {
    const text = textEl.value.trim();
    if (!text) return;
    textEl.value = '';
    try {
      await fetch('/api/post', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: fromEl.value, text })
      });
    } catch (_) { textEl.value = text; }
  }
  form.addEventListener('submit', (e) => { e.preventDefault(); send(); });
  textEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # quiet

    def _send(self, code, body: bytes, ctype="text/plain; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/" or path == "/index.html":
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/api/messages":
            out = []
            try:
                with open(LOG, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        line = line.strip()
                        if line:
                            try:
                                m = json.loads(line); m["i"] = i; out.append(m)
                            except json.JSONDecodeError:
                                pass
            except FileNotFoundError:
                pass
            self._send(200, json.dumps(out).encode("utf-8"), "application/json")
        elif path == "/api/stream":
            self._stream()
        else:
            self._send(404, b"not found")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/post":
            self._send(404, b"not found"); return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
            text = str(data.get("text", "")).strip()
            sender = str(data.get("from", "host"))
            if not text:
                self._send(400, b'{"error":"empty"}', "application/json"); return
            append_message(sender, text)
            self._send(200, b'{"ok":true}', "application/json")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send(400, b'{"error":"bad json"}', "application/json")

    def _stream(self):
        """Server-Sent Events: replay the whole log, then tail for new lines."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            with open(LOG, "r", encoding="utf-8") as f:
                idx = 0
                last_beat = time.time()
                while True:
                    pos = f.tell()
                    line = f.readline()
                    if line and line.endswith("\n"):
                        idx += 1
                        try:
                            m = json.loads(line)
                            m["i"] = idx
                            payload = "data: " + json.dumps(m, ensure_ascii=False) + "\n\n"
                            self.wfile.write(payload.encode("utf-8"))
                            self.wfile.flush()
                        except json.JSONDecodeError:
                            pass
                    else:
                        # Partial or no line: rewind and wait for more.
                        f.seek(pos)
                        time.sleep(0.4)
                        if time.time() - last_beat > 15:
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                            last_beat = time.time()
        except (BrokenPipeError, ConnectionResetError):
            return  # client went away


def main():
    ensure_log()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.daemon_threads = True
    url = f"http://localhost:{PORT}"
    print(f"Squawk panel running at {url}")
    print(f"Log: {LOG}")
    print("Post from a terminal:  python say.py claude \"your message\"")
    print("Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
        server.shutdown()


if __name__ == "__main__":
    main()
