# ^dashboard
> **Purpose:** Launch the Axis Dashboard in a browser.

1. Verify `_Axis/Dashboard/index.html` and `_Axis/Dashboard/server.py` exist. If either is missing: offer to restore it per [Practices > Dashboard]; if User declines, STOP.

2. Note: the Dashboard is the live view of the project - it reads approved project files continuously and refreshes itself every 30 seconds. It must therefore be served over HTTP; opening `index.html` as a `file://` page blocks file reads and shows nothing. The bundled server is read-only, binds only to a loopback IP, filters directory listings, rejects traversal and symlinks, and denies `_Axis/Secrets/`, `_Temp/`, `.git/`, host configuration, and every path outside the Dashboard read contract. Never substitute a general-purpose project-root file server. If User cannot run the bundled server, offer `^status` instead.

3. Read `host-shell` under [Practices > Flags > Reading Flags]. If it is not valid `yes`: you cannot start a server, but User may still be able to. Give them the manual steps - from the project root run `python3 _Axis/Dashboard/server.py --port 8000`, then open `http://127.0.0.1:8000/_Axis/Dashboard/` - and GOTO step 6. If Python 3 is unavailable or User cannot run the server, offer `^status` and STOP.

4. If your shell runs on User's machine (e.g., a local CLI host). If you cannot confirm that - on hosted or cloud harnesses, `localhost` is usually the sandbox, not User's machine - treat the shell as remote and GOTO step 5, because a server started in a sandbox is unreachable to User. Otherwise:
	- a. Pick a free port, starting at 8000 (if busy, try 8001, 8002, ...).
	- b. From the project root, run in the background: `python3 _Axis/Dashboard/server.py --port {port}`. If `python3` is unavailable, use `python` only when it is Python 3; otherwise offer `^status`. Never fall back to a general-purpose static server.
	- c. Open `http://127.0.0.1:{port}/_Axis/Dashboard/` in User's browser (`open` on macOS, `xdg-open` on Linux, `start` on Windows), or give User the link.
	- d. Tell User how to stop the server when done (kill the process, or close its terminal).
	- e. GOTO step 6.

5. If your shell is sandboxed or remote (your `localhost` is not User's machine): do NOT start the server yourself - give User this one-liner to run in their own terminal from the project root, and the link to open:
	- `python3 _Axis/Dashboard/server.py --port 8000`
	- `http://127.0.0.1:8000/_Axis/Dashboard/`

6. Remind User that the Dashboard refreshes itself every 30 seconds (a Reload button forces one immediately and visibly acknowledges the refresh), stays live only while the server runs, and is available only on the machine running that server. They can ask you to revise and extend it to fit the project (see [Practices > Dashboard]). STOP.
