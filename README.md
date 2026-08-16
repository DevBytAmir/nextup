<div align="center">

# NextUp

Self-hosted, realtime take-a-number queueing system.

![CI](https://github.com/DevBytAmir/nextup/actions/workflows/ci.yml/badge.svg)
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

</div>

---

NextUp runs a shared queue for any walk-up service line: one screen issues
sequential numbers, two counters serve customers from that single line, a
TV or monitor shows live queue status, and an admin screen gives full
manual control.

<div align="center">

| Page | URL | Access |
|:---|:---:|:---:|
| Issue number | `/number` | PIN |
| Counter | `/counter` | PIN |
| Admin | `/admin` | PIN |
| TV display | `/tv` | Public, read-only |

</div>

## Architecture

- **Backend** — FastAPI and Uvicorn, single process, a single `asyncio.Lock`
  around every ticket mutation so two "Call Next" clicks can never claim the
  same ticket.
- **Realtime** — one `/ws` WebSocket endpoint; every mutation broadcasts the
  updated queue to all connected pages.
- **Persistence** — a single `data/state.json` file, loaded at startup and
  rewritten after every mutation.
- **Frontend** — plain HTML, CSS, and vanilla JavaScript. No build step, no
  framework.

## Getting started

Requires Python 3.11 or newer.

```bash
python -m venv .venv
./.venv/bin/pip install -e .[dev]      # .venv\Scripts\pip on Windows
./.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Then open `http://127.0.0.1:8000/number`, `/counter`, `/admin`, and `/tv`.

Default PINs — numbering `1111`, counters `2222` / `3333`, admin `9999`.
Change them from the admin settings panel, or by editing `data/state.json`
directly before first run.

## Testing

```bash
./.venv/bin/python -m ruff check backend
./.venv/bin/python -m ruff format --check backend
./.venv/bin/python -m pytest backend/tests -v
```

Ticket claiming, reordering, skip/requeue/delete, PIN auth, and the
no-double-claim guarantee are covered by automated tests. The frontend
pages are covered by a manual smoke test that walks through issuing a
number, calling and completing it, skipping and requeuing a ticket,
deleting a ticket, reordering the waiting list, confirming a wrong PIN is
rejected on `/number`, `/counter`, and `/admin`, and confirming `/tv`
updates live across two browser windows with no refresh and never exposes
a PIN in its WebSocket traffic.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

Released under the [Apache License 2.0](LICENSE).
