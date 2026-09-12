# eazykill

List open macOS GUI apps and quit or force-quit them from the terminal.

A Dock-level view of what's actually running — not 300 background daemons —
with a one-key graceful quit and a force-kill fallback.

## Requirements

- macOS
- Python 3.8+ (stdlib only, no dependencies)

## Install

```sh
chmod +x eazykill
# optional: put it on your PATH
ln -s "$(pwd)/eazykill" /usr/local/bin/eazykill
```

## Usage

```sh
./eazykill
```

## Keys

| Key | Action |
| --- | --- |
| `↑` / `↓` | move selection |
| `/` | search / filter by name |
| `k` | graceful quit (asks the app to close) |
| `K` or `Ctrl-K` | force kill (`SIGKILL`) |
| `q` / `Esc` | exit |

The terminal that launched eazykill is hidden from the list so you can't
accidentally quit the very thing running it.

## How it works

- App list, PID, and launch time come from `lsappinfo` (LaunchServices).
- Graceful quit is `osascript … to quit` (by bundle id when available); the
  process is then polled to confirm it actually exited before success is
  reported.
- Force quit is `kill -9 <pid>`.

## Known limitations

- **`lsappinfo` is a semi-private API.** It's a LaunchServices diagnostic tool
  whose text output isn't a documented, stable contract and could change
  across macOS versions. This is the main portability risk.
- **Duplicate app names** (e.g. multiple Firefox instances) each get their own
  row. Graceful quit targets the front instance; force kill targets the exact
  PID shown.
- **Terminal hiding** relies on the terminal being an ancestor process, so it
  won't work inside `tmux`/`screen`/detached sessions.
- **macOS only** — no Linux/Wayland backend.
- Quitting `Finder` just relaunches it (expected macOS behavior).

## Tests

```sh
python3 -m unittest discover -s tests
```

## License

MIT — see [LICENSE](LICENSE).
