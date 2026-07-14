# FocusFlow — Personal Productivity OS

A premium, fully offline desktop productivity suite built with **Python 3.13+** and **PySide6**.

Inspired by Notion, TickTick, Todoist, and Motion — with zero cloud dependency. All data lives in local JSON files.

## Features

- **Dashboard** — greeting, progress ring, streaks, timers, quotes, charts, quick-add
- **Tasks** — full CRUD, priorities, tags, archive, favorite, duplicate, search/filter/sort, timers
- **Projects** — colored projects with live progress %
- **Habits** — daily/weekly/monthly, streaks, calendar heatmap
- **Pomodoro** — focus / short / long / custom with desktop notifications & per-second autosave
- **Calendar** — month & week views with task and deadline indicators
- **Notes** — markdown notes with folders, pins, and auto-save
- **Statistics** — daily/weekly/monthly/yearly Matplotlib charts + productivity score 0–100
- **History** — complete action audit log
- **Extras** — journal, mood, water, workout, reading, coding, LeetCode, GitHub (manual), study, prayer, finance, scratch pad, sticky notes, countdowns, XP/levels/badges
- **Backup** — automatic daily backups (last 30 retained) + restore + corrupt JSON recovery
- **Settings** — accent color, font size, notifications, sounds, Pomodoro times, Windows startup

## Requirements

- Python 3.13 or newer
- Windows 10/11 (startup integration supported)

## Install

```bash
cd FocusFlow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New task |
| `Ctrl+F` | Search tasks |
| `Ctrl+S` | Manual save all stores |
| `Delete` | Delete selected task |
| `Space` | Start / pause / resume timer |
| `Ctrl+1`…`9` | Jump to sidebar pages |

## Architecture

| Layer | Role |
|-------|------|
| **Models** (`src/models`) | Dataclasses with JSON (de)serialization |
| **Services** (`src/services`) | Persistence, timers, stats, notifications |
| **UI / Widgets** (`src/ui`, `src/widgets`) | PySide6 views and reusable controls |

All state auto-saves to JSON after every change. No SQL. No network.

## Data files

Everything under `data/`:

`tasks.json` · `projects.json` · `habits.json` · `notes.json` · `timers.json` · `stats.json` · `history.json` · `settings.json` · `extras.json` · `achievements.json` · `backups/`

## License

Private / commercial use — all rights reserved.
