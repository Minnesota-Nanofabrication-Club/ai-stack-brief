#!/usr/bin/env python3
"""Local preview server for ai-stack-brief.

GitHub Pages serves a tree built as `site/` with `briefs/` copied to
`site/briefs/`. This server reproduces that composition *without* copying
anything into the repo: it maps request paths onto the two source
directories, so `./briefs/index.json` resolves exactly the way it will in
production and nothing extra ever shows up in `git status`.

    /               -> site/index.html
    /style.css      -> site/style.css
    /briefs/...     -> briefs/...

Usage:
    python3 scripts/serve.py
    python3 scripts/serve.py --port 8080
    python3 scripts/serve.py --open          # also open a browser

Standard library only.
"""

from __future__ import annotations

import argparse
import errno
import functools
import os
import posixpath
import socket
import sys
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(REPO_ROOT, "site")
BRIEFS_DIR = os.path.join(REPO_ROOT, "briefs")
DEFAULT_PORT = 8000


class ComposedHandler(SimpleHTTPRequestHandler):
    """Serves site/ at the root with briefs/ mounted at /briefs/."""

    site_dir = SITE_DIR
    briefs_dir = BRIEFS_DIR

    def translate_path(self, path: str) -> str:
        # Strip query/fragment, decode, normalise — same preamble as the stdlib
        # handler, but we choose the root per-request instead of using cwd.
        path = path.split("?", 1)[0].split("#", 1)[0]
        trailing_slash = path.endswith("/")
        try:
            path = urllib.parse.unquote(path, errors="surrogatepass")
        except UnicodeDecodeError:
            path = urllib.parse.unquote(path)
        path = posixpath.normpath(path)

        # A percent-encoded NUL (%00) survives unquote and then makes
        # os.path.realpath() raise ValueError below, which escapes translate_path,
        # kills the worker thread, and drops the connection with no response at
        # all. Reject it — along with the other C0 control bytes, none of which
        # belong in a path — and let the normal 404 path handle it.
        if any(ch in path for ch in ("\x00",)) or any(ord(ch) < 32 for ch in path):
            return os.path.join(os.path.realpath(self.site_dir), "__forbidden__")

        parts = [p for p in path.split("/") if p and p not in (".", "..")]

        if parts and parts[0] == "briefs":
            root, parts = self.briefs_dir, parts[1:]
        else:
            root = self.site_dir

        resolved = os.path.join(root, *parts)
        if trailing_slash:
            resolved += os.sep

        # Defence in depth: never escape the chosen root.
        real_root = os.path.realpath(root)
        real_target = os.path.realpath(resolved.rstrip(os.sep) or root)
        if real_target != real_root and not real_target.startswith(real_root + os.sep):
            return os.path.join(real_root, "__forbidden__")
        return resolved

    def end_headers(self) -> None:
        # Preview server: never let the browser cache a brief you just edited.
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("  %s %s\n" % (self.log_date_time_string(), fmt % args))


def guess_lan_ip() -> str | None:
    """Best-effort local IP so you can open the preview on your phone."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.2)
            s.connect(("192.0.2.1", 9))  # TEST-NET-1, no packets actually sent
            return s.getsockname()[0]
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="serve.py",
        description="Preview site/ + briefs/ the way GitHub Pages will serve them.",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"port to listen on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--host", default="127.0.0.1",
        help="address to bind (default: 127.0.0.1; use 0.0.0.0 to reach it from your phone)",
    )
    parser.add_argument(
        "--open", action="store_true", dest="open_browser",
        help="open the preview in your default browser",
    )
    args = parser.parse_args(argv)

    missing = [d for d in (SITE_DIR, BRIEFS_DIR) if not os.path.isdir(d)]
    if missing:
        for d in missing:
            print(f"ERROR  missing directory: {d}", file=sys.stderr)
        print("       Run this from a full checkout of the repo.", file=sys.stderr)
        return 2

    if not os.path.isfile(os.path.join(SITE_DIR, "index.html")):
        print(f"ERROR  {os.path.join(SITE_DIR, 'index.html')} does not exist.", file=sys.stderr)
        return 2

    if not os.path.isfile(os.path.join(BRIEFS_DIR, "index.json")):
        print(
            "WARN   briefs/index.json is missing — the app will show nothing.\n"
            "       Generate it with: python3 scripts/build_index.py",
            file=sys.stderr,
        )

    if not (0 < args.port < 65536):
        print(f"ERROR  --port {args.port} is not a valid port number.", file=sys.stderr)
        return 2

    handler = functools.partial(ComposedHandler, directory=SITE_DIR)
    ThreadingHTTPServer.allow_reuse_address = True

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        if exc.errno in (errno.EADDRINUSE, errno.EACCES):
            if exc.errno == errno.EADDRINUSE:
                print(
                    f"ERROR  port {args.port} is already in use on {args.host}.\n"
                    f"       Something else is listening there — another copy of this\n"
                    f"       server, or another dev server.\n"
                    f"\n"
                    f"       Pick a different port:   python3 scripts/serve.py --port {args.port + 1}\n"
                    f"       Or find the culprit:     lsof -nP -iTCP:{args.port} -sTCP:LISTEN",
                    file=sys.stderr,
                )
            else:
                print(
                    f"ERROR  not allowed to bind port {args.port} "
                    f"(ports below 1024 need root). Try --port 8000.",
                    file=sys.stderr,
                )
            return 1
        print(f"ERROR  could not start the server: {exc}", file=sys.stderr)
        return 1

    display_host = "localhost" if args.host in ("127.0.0.1", "0.0.0.0", "::") else args.host
    url = f"http://{display_host}:{args.port}/"

    print("ai-stack-brief preview")
    print(f"  site/    -> {SITE_DIR}")
    print(f"  briefs/  -> {BRIEFS_DIR}  (mounted at /briefs/)")
    print()
    print(f"  {url}")
    if args.host == "0.0.0.0":
        lan = guess_lan_ip()
        if lan:
            print(f"  http://{lan}:{args.port}/   (from another device on this network)")
    print()
    print("  Ctrl-C to stop.")
    print()

    if args.open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
