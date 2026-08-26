#!/usr/bin/env python3
"""Loopback-only, read-only HTTP server for the Axis Dashboard."""

from __future__ import annotations

import argparse
import html
import ipaddress
import mimetypes
import os
import socket
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


BLOCKED_PARTS = {
    "Secrets",
    "_Temp",
    "_Trash",
    ".git",
    ".obsidian",
    ".claude",
    ".codex",
    ".cursor",
    ".gemini",
    ".vscode",
    ".trash",
    "node_modules",
}
AXIS_RECORD_FAMILIES = {
    "Agents",
    "Tracking",
    "Tasks",
    "Followups",
    "Reminders",
    "Ideas",
    "Notes",
    "Logs",
    "Status",
    "Snapshots",
    "CX",
    "Audit",
}
AXIS_ROOT_FILES = {"CHANGELOG.md", "PROJECT.md", "SETTINGS.md", "PLAN.md", "TASKS.md"}
DASHBOARD_FILES = {
    "index.html",
    "mermaid-11.16.1.min.js",
    "plan-diagram.svg",
    "plan-diagram.png",
    "plan-diagram.mermaid",
}
FLAG_FILES = {
    "model",
    "host-spawn",
    "host-parallel",
    "host-shell",
    "host-local-llm",
    "host-cloud-sync",
    "host-storage",
    "local-aptitude",
}
WIKI_ADMIN_FILES = {
    "Library-Index.md",
    "Library-Activity.md",
    "Library-Status.md",
}


class DeniedPath(ValueError):
    """Raised when a request is outside the Dashboard's read contract."""


def normalize_request_path(target: str) -> tuple[tuple[str, ...], bool]:
    """Return decoded path components and whether the URL requested a directory."""
    raw = urlsplit(target).path
    if len(raw) > 4096 or not raw.startswith("/"):
        raise DeniedPath("invalid request path")

    decoded = raw
    for _ in range(4):
        newer = unquote(decoded)
        if newer == decoded:
            break
        decoded = newer
    if "%" in decoded or "\\" in decoded or "\x00" in decoded:
        raise DeniedPath("ambiguous path encoding")

    directory = decoded.endswith("/")
    parts = tuple(part for part in decoded.split("/") if part)
    if any(part in {".", ".."} or part.startswith(".") or part in BLOCKED_PARTS for part in parts):
        raise DeniedPath("blocked path")
    return parts, directory


def is_allowed_file(parts: tuple[str, ...]) -> bool:
    if len(parts) == 2 and parts[0] == "_Axis" and parts[1] in AXIS_ROOT_FILES:
        return True
    if len(parts) == 3 and parts[:2] == ("_Axis", "Dashboard") and parts[2] in DASHBOARD_FILES:
        return True
    if len(parts) == 3 and parts[:2] == ("_Axis", "Flags") and parts[2] in FLAG_FILES:
        return True
    if (
        len(parts) == 3
        and parts[0] == "_Axis"
        and parts[1] in AXIS_RECORD_FAMILIES
        and parts[2].endswith(".md")
    ):
        return True
    # A `.kill` tombstone beside an Agents Marker means that session is dead at any
    # age; served so the Agents card can mark killed sessions as stopped.
    if len(parts) == 3 and parts[:2] == ("_Axis", "Agents") and parts[2].endswith(".kill"):
        return True
    if len(parts) == 3 and parts[:2] == ("_Axis", "Wiki") and parts[2] in WIKI_ADMIN_FILES:
        return True
    return False


def is_record_directory(parts: tuple[str, ...]) -> bool:
    return len(parts) == 2 and parts[0] == "_Axis" and parts[1] in AXIS_RECORD_FAMILIES


def is_lock_directory(parts: tuple[str, ...]) -> bool:
    if not parts or not parts[-1].endswith(".lock"):
        return False
    parent = parts[:-1]
    return parent in {(), ("_Axis",)} or is_record_directory(parent)


def is_browsable_directory(parts: tuple[str, ...]) -> bool:
    if parts in {(), ("_Axis",)} or is_record_directory(parts):
        return True
    if parts == ("_Axis", "Dashboard"):
        return True
    if parts == ("_Axis", "Requests"):
        return True
    return False


def contains_symlink(root: Path, parts: tuple[str, ...]) -> bool:
    current = root
    for part in parts:
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return True
    return False


def resolve_under_root(root: Path, parts: tuple[str, ...]) -> Path:
    root = root.resolve()
    if contains_symlink(root, parts):
        raise DeniedPath("symbolic links are not served")
    candidate = root.joinpath(*parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise DeniedPath("path leaves project root") from exc
    return resolved


def is_allowed_file_for_root(root: Path, parts: tuple[str, ...]) -> bool:
    return is_allowed_file(parts)


def visible_directory_entries(root: Path, parts: tuple[str, ...]) -> list[tuple[str, bool]]:
    directory = resolve_under_root(root, parts)
    if not directory.is_dir():
        raise FileNotFoundError

    entries: list[tuple[str, bool]] = []
    for child in directory.iterdir():
        name = child.name
        child_parts = parts + (name,)
        if name.startswith(".") or name in BLOCKED_PARTS or child.is_symlink():
            continue
        try:
            if child.is_dir():
                if is_lock_directory(child_parts):
                    entries.append((name, True))
                elif is_record_directory(parts):
                    continue
                elif is_browsable_directory(child_parts):
                    entries.append((name, True))
            elif child.is_file() and (
                is_allowed_file_for_root(root, child_parts)
                # Requests are listed by NAME only - the Dashboard's queue count;
                # request bodies stay outside the read contract.
                or (parts == ("_Axis", "Requests") and name.endswith(".md"))
            ):
                entries.append((name, False))
        except OSError:
            continue
    return sorted(entries, key=lambda item: (not item[1], item[0].lower()))


class AxisDashboardHandler(BaseHTTPRequestHandler):
    server_version = "AxisDashboard/1"

    @property
    def project_root(self) -> Path:
        return self.server.project_root  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def do_GET(self) -> None:
        self._serve(head_only=False)

    def do_HEAD(self) -> None:
        self._serve(head_only=True)

    def do_POST(self) -> None:
        self._method_not_allowed()

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def do_PATCH(self) -> None:
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        self.send_response(405)
        self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve(self, head_only: bool) -> None:
        try:
            parts, directory_request = normalize_request_path(self.path)
            if parts == ("_Axis", "Dashboard") and directory_request:
                self._serve_file(parts + ("index.html",), head_only)
                return
            if is_lock_directory(parts) and directory_request:
                if not head_only:
                    raise DeniedPath("lock contents are not served")
                self._serve_lock_head(parts)
                return
            if directory_request and is_browsable_directory(parts):
                self._serve_listing(parts, head_only)
                return
            if not directory_request and is_allowed_file_for_root(self.project_root, parts):
                self._serve_file(parts, head_only)
                return
            raise DeniedPath("path is outside the Dashboard read contract")
        except DeniedPath as exc:
            self.send_error(403, str(exc))
        except FileNotFoundError:
            self.send_error(404, "not found")
        except OSError:
            self.send_error(404, "not found")

    def _serve_lock_head(self, parts: tuple[str, ...]) -> None:
        path = resolve_under_root(self.project_root, parts)
        if not path.is_dir():
            raise FileNotFoundError
        stat = path.stat()
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Last-Modified", formatdate(stat.st_mtime, usegmt=True))
        self.end_headers()

    def _serve_file(self, parts: tuple[str, ...], head_only: bool) -> None:
        path = resolve_under_root(self.project_root, parts)
        if not path.is_file():
            raise FileNotFoundError
        stat = path.stat()
        suffix = path.suffix.lower()
        if suffix in {".md", ".mermaid", ".kill", ""}:
            content_type = "text/plain; charset=utf-8"
        else:
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(stat.st_size))
        self.send_header("Last-Modified", formatdate(stat.st_mtime, usegmt=True))
        if parts == ("_Axis", "Dashboard", "index.html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; connect-src 'self'; img-src 'self' data:; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
            )
        elif suffix == ".svg":
            self.send_header("Content-Security-Policy", "default-src 'none'; sandbox")
        self.end_headers()
        if not head_only:
            with path.open("rb") as source:
                while chunk := source.read(64 * 1024):
                    self.wfile.write(chunk)

    def _serve_listing(self, parts: tuple[str, ...], head_only: bool) -> None:
        entries = visible_directory_entries(self.project_root, parts)
        rows = []
        for name, is_directory in entries:
            shown = name + ("/" if is_directory else "")
            href = quote(name) + ("/" if is_directory else "")
            rows.append(f'<li><a href="{href}">{html.escape(shown)}</a></li>')
        title = "/" + "/".join(parts) + ("/" if parts else "")
        body = (
            "<!doctype html><meta charset=\"utf-8\">"
            f"<title>{html.escape(title)}</title><ul>{''.join(rows)}</ul>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)


class AxisDashboardServer(ThreadingHTTPServer):
    daemon_threads = True
    project_root: Path


class AxisDashboardServerV6(AxisDashboardServer):
    address_family = socket.AF_INET6


def create_server(bind: str, port: int, root: Path) -> AxisDashboardServer:
    try:
        address = ipaddress.ip_address(bind)
    except ValueError as exc:
        raise ValueError("--bind must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("--bind must be loopback; use 127.0.0.1 or ::1")

    root = root.resolve()
    if not (root / "_Axis" / "Dashboard" / "index.html").is_file():
        raise ValueError("project root does not contain _Axis/Dashboard/index.html")
    server_class = AxisDashboardServerV6 if address.version == 6 else AxisDashboardServer
    server = server_class((bind, port), AxisDashboardHandler)
    server.project_root = root
    return server


def main() -> int:
    default_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Serve the Axis Dashboard over loopback only.")
    parser.add_argument("--bind", default="127.0.0.1", help="loopback IP: 127.0.0.1 or ::1")
    parser.add_argument("--port", type=int, default=8000, help="TCP port (default: 8000)")
    parser.add_argument("--root", type=Path, default=default_root, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    try:
        server = create_server(args.bind, args.port, args.root)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    actual_port = server.server_address[1]
    host = f"[{args.bind}]" if ":" in args.bind else args.bind
    url = f"http://{host}:{actual_port}/_Axis/Dashboard/"
    print(f"Axis Dashboard: {url}")
    print("Serving approved read-only paths only. Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
