# eazykill

List and quit macOS GUI apps from the terminal.

## Requirements

- macOS
- Python 3.8+

## Install

- `chmod +x eazykill`
- Optional: `ln -s "$(pwd)/eazykill" /usr/local/bin/eazykill`

## Usage

- `./eazykill`

## Keys

- `↑` / `↓` — move selection
- `/` — search by name
- `k` — graceful quit
- `K` / `Ctrl-K` — force kill
- `q` / `Esc` — exit

## Notes

- Shows foreground (Dock) apps: name, PID, running time.
- Hides the terminal running it.
- App list comes from `lsappinfo` (LaunchServices). Semi-private API, not a stable contract.
- Graceful quit is `osascript`; force kill is `kill -9`.
- Duplicate names (e.g. two Firefox) each get a row; force kill uses the exact PID.
- Terminal hiding breaks in tmux/screen/detached sessions.
- macOS only.
- Quitting Finder relaunches it.

## Tests

- `python3 -m unittest discover -s tests`

## License

- MIT — see LICENSE
